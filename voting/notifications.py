# voting/notifications.py - Notification system for elections

from __future__ import annotations

from datetime import timedelta
from typing import List, Optional

from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

from celery import shared_task

from .models import Election, Notification, VoterProfile
from .utils import send_notification


# ═══════════════════════════════════════════════════════════════
# Election Notifications
# ═══════════════════════════════════════════════════════════════

def notify_voters_election_starting(election: Election) -> None:
    """Notify all eligible voters that election is starting in X minutes"""
    try:
        # Get all eligible voters for this election's constituencies
        eligible_voters = VoterProfile.objects.filter(
            constituency__election=election,
            is_verified=True,
            email_verified=True,
            is_admin=False,
        ).values_list('user', flat=True)

        users = User.objects.filter(id__in=eligible_voters)

        for user in users:
            send_notification(
                user=user,
                ntype=Notification.Type.ELECTION_START,
                title=f"Election '{election.title}' Starting",
                message=f"The election '{election.title}' will start at {election.start_at.strftime('%Y-%m-%d %H:%M')} UTC+5:45",
                election=election,
                send_email=True,
                send_sms=False,
            )
    except Exception as e:
        print(f"Failed to notify voters: {e}")


def notify_voting_reminder(election: Election) -> None:
    """Remind voters to cast their vote during ongoing election"""
    try:
        # Get voters who haven't voted yet
        from .models import VoterParticipation

        eligible_voters = VoterProfile.objects.filter(
            constituency__election=election,
            is_verified=True,
            email_verified=True,
            is_admin=False,
        ).values_list('user_id', flat=True)

        voted_users = VoterParticipation.objects.filter(
            election=election,
            has_voted=True
        ).values_list('voter_id', flat=True)

        # Get voters who haven't voted
        not_voted = set(eligible_voters) - set(voted_users)
        users = User.objects.filter(id__in=not_voted)

        for user in users:
            send_notification(
                user=user,
                ntype=Notification.Type.VOTING_REMINDER,
                title="Don't miss your vote!",
                message=f"Election '{election.title}' is ongoing. Cast your vote before {election.end_at.strftime('%Y-%m-%d %H:%M')} UTC+5:45",
                election=election,
                send_email=True,
                send_sms=False,
            )
    except Exception as e:
        print(f"Failed to send voting reminder: {e}")


def notify_election_results(election: Election) -> None:
    """Notify voters that election results are available"""
    try:
        # Notify all users who participated
        from .models import VoterParticipation

        voters = VoterParticipation.objects.filter(
            election=election,
            has_voted=True
        ).values_list('voter_id', flat=True)

        users = User.objects.filter(id__in=voters)

        for user in users:
            send_notification(
                user=user,
                ntype=Notification.Type.RESULT_ANNOUNCEMENT,
                title=f"Results: {election.title}",
                message=f"Results for '{election.title}' are now available. View them in your dashboard.",
                election=election,
                send_email=True,
                send_sms=False,
            )
    except Exception as e:
        print(f"Failed to notify results: {e}")


# ═══════════════════════════════════════════════════════════════
# Celery Scheduled Tasks (if celery is enabled)
# ═══════════════════════════════════════════════════════════════

@shared_task(bind=True, max_retries=3)
def send_election_starting_notification(self, election_id: int) -> None:
    """Celery task to send election starting notifications"""
    try:
        election = Election.objects.get(id=election_id)
        notify_voters_election_starting(election)
    except Election.DoesNotExist:
        print(f"Election {election_id} not found")
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_voting_reminder_notification(self, election_id: int) -> None:
    """Celery task to send voting reminder notifications"""
    try:
        election = Election.objects.get(id=election_id)
        if election.is_running:
            notify_voting_reminder(election)
    except Election.DoesNotExist:
        print(f"Election {election_id} not found")
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_results_notification(self, election_id: int) -> None:
    """Celery task to send election results notifications"""
    try:
        election = Election.objects.get(id=election_id)
        if election.has_ended:
            notify_election_results(election)
    except Election.DoesNotExist:
        print(f"Election {election_id} not found")
    except Exception as exc:
        self.retry(exc=exc, countdown=60)


@shared_task
def cleanup_expired_notifications() -> None:
    """Celery task to clean up old notifications (keep last 30 days)"""
    try:
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=30)
        Notification.objects.filter(read_at__lt=cutoff_date).delete()
    except Exception as e:
        print(f"Failed to cleanup notifications: {e}")


@shared_task
def cleanup_expired_otp() -> None:
    """Celery task to clean up expired OTP codes"""
    try:
        VoterProfile.objects.filter(
            otp_expires_at__lt=timezone.now(),
            otp_code__isnull=False
        ).update(otp_code='', otp_expires_at=None)
    except Exception as e:
        print(f"Failed to cleanup OTPs: {e}")


