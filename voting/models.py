from __future__ import annotations

import hashlib
import json
import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Election(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        RUNNING = "RUNNING", "Running"
        ENDED = "ENDED", "Ended"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValidationError({"end_at": "end_at must be after start_at"})

    def sync_status(self, now=None) -> str:
        """
        Keep status aligned with time unless still DRAFT.
        - If DRAFT: stays DRAFT unless manually changed in admin.
        - If RUNNING: auto-end when time passed.
        """
        now = now or timezone.now()

        if self.status == self.Status.DRAFT:
            return self.status

        if self.start_at <= now <= self.end_at:
            if self.status != self.Status.RUNNING:
                self.status = self.Status.RUNNING
                self.save(update_fields=["status"])
        elif now > self.end_at:
            if self.status != self.Status.ENDED:
                self.status = self.Status.ENDED
                self.save(update_fields=["status"])
        else:
            # now < start_at
            if self.status != self.Status.DRAFT:
                self.status = self.Status.DRAFT
                self.save(update_fields=["status"])

        return self.status

    @property
    def is_running(self) -> bool:
        now = timezone.now()
        return self.status == self.Status.RUNNING and self.start_at <= now <= self.end_at

    @property
    def has_ended(self) -> bool:
        now = timezone.now()
        return self.status == self.Status.ENDED or now > self.end_at

    def __str__(self):
        return self.title


class District(models.Model):
    name_en = models.CharField(max_length=100, unique=True)
    name_np = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name_en


class Constituency(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="constituencies")
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="constituencies")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["election", "code"], name="uniq_constituency_code_per_election"),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Party(models.Model):
    name_en = models.CharField(max_length=200)
    name_np = models.CharField(max_length=200, blank=True)
    abbreviation = models.CharField(max_length=20)
    symbol_text = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.abbreviation


class Candidate(models.Model):
    full_name_en = models.CharField(max_length=200)
    full_name_np = models.CharField(max_length=200, blank=True)
    party = models.ForeignKey(Party, on_delete=models.PROTECT, related_name="candidates")
    constituency = models.ForeignKey(Constituency, on_delete=models.CASCADE, related_name="candidates")
    photo = models.ImageField(upload_to="candidate_photos/", blank=True, null=True)

    def __str__(self):
        return f"{self.full_name_en} [{self.party.abbreviation}]"


class VoterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="voter_profile")

    # IMPORTANT: do NOT clash with District.constituencies related_name
    district = models.ForeignKey(
        District,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="voter_profiles",
    )

    citizenship_id = models.CharField(max_length=40, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_verified = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)  # Admins cannot vote

    # NEW FIELDS: Enhanced authentication
    unique_voter_id = models.CharField(max_length=50, unique=True, blank=True)  # Auto-generated
    date_of_birth = models.DateField(null=True, blank=True)  # Age verification
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)  # NEW
    email_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=10, blank=True)  # Temporary OTP storage
    otp_expires_at = models.DateTimeField(null=True, blank=True)
    google_oauth_id = models.CharField(max_length=255, blank=True, unique=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    login_attempts = models.IntegerField(default=0)
    login_locked_until = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)  # Additional data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    constituency = models.ForeignKey(
        Constituency,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="voter_profiles",
    )

    def __str__(self):
        return f"VoterProfile({self.user.username})"

    @property
    def age(self):
        """Calculate age from date of birth"""
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def is_eligible_to_vote(self):
        """Check if voter is eligible (age >= 18, verified, not admin)"""
        return (
            self.age and self.age >= 18 and
            self.is_verified and
            self.email_verified and
            not self.is_admin and
            self.constituency_id is not None
        )


class VoterParticipation(models.Model):
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="participations")
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="participations")
    has_voted = models.BooleanField(default=False)
    voted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["voter", "election"], name="uniq_voter_election_participation"),
        ]

    def __str__(self):
        return f"{self.voter_id}:{self.election_id} voted={self.has_voted}"


class EncryptedBallot(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="ballots")
    constituency = models.ForeignKey(Constituency, on_delete=models.CASCADE, related_name="ballots")

    # NOTE: If migration complains about adding a unique field, do the 2-step migration:
    # 1) remove unique=True, migrate
    # 2) add unique=True, migrate
    receipt_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    encrypted_payload = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class VoteVerification(models.Model):
    """Track admin verification status for each vote"""
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    ballot = models.OneToOneField(EncryptedBallot, on_delete=models.CASCADE, related_name="verification")
    voter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="vote_verifications")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="votes_verified")
    verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["created_at"]

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"VoteVerification({self.voter.username if self.voter else 'Unknown'}) - {self.status}"


class ResultTally(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="tallies")
    constituency = models.ForeignKey(Constituency, on_delete=models.CASCADE, related_name="tallies")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="tallies")
    votes = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["election", "constituency", "candidate"], name="uniq_tally_triplet"),
        ]


class AuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=50)
    object_type = models.CharField(max_length=80)
    object_id = models.CharField(max_length=80, blank=True)
    meta_json = models.JSONField(default=dict, blank=True)

    ip = models.GenericIPAddressField(null=True, blank=True)
    ua = models.TextField(blank=True)

    prev_hash = models.CharField(max_length=64, blank=True)
    hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def compute_hash(self) -> str:
        payload = {
            "prev_hash": self.prev_hash or "",
            "actor_id": self.actor_id or "",
            "action": self.action,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "meta_json": self.meta_json,
            "ip": self.ip or "",
            "ua": self.ua or "",
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }
        s = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    def save(self, *args, **kwargs):
        if not self.pk:
            last = AuditLog.objects.order_by("-id").first()
            self.prev_hash = last.hash if last else ""
        super().save(*args, **kwargs)
        if not self.hash:
            self.hash = self.compute_hash()
            super().save(update_fields=["hash"])


# OPTIONAL: Only keep this if some other file imports it.
# But with UUIDField(default=uuid.uuid4), you DO NOT NEED it.
def make_receipt_uuid() -> str:
    return str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════
# NEW MODELS - Enhanced Features
# ═══════════════════════════════════════════════════════════════

class CandidateMetadata(models.Model):
    """Extended candidate information"""
    candidate = models.OneToOneField(Candidate, on_delete=models.CASCADE, related_name="metadata")
    biography = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    policies = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    social_media = models.JSONField(default=dict, blank=True)  # {twitter, facebook, etc}
    video_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Metadata for {self.candidate.full_name_en}"


class Notification(models.Model):
    """User notifications for elections and voting"""
    class Type(models.TextChoices):
        ELECTION_START = "ELECTION_START", "Election Starting"
        VOTING_REMINDER = "VOTING_REMINDER", "Voting Reminder"
        RESULT_ANNOUNCEMENT = "RESULT_ANNOUNCEMENT", "Results Available"
        ADMIN_MESSAGE = "ADMIN_MESSAGE", "Admin Message"
        PROFILE_UPDATE = "PROFILE_UPDATE", "Profile Update Required"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    election = models.ForeignKey(Election, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    ntype = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    sent_via = models.JSONField(default=dict)  # {email: true, sms: false, in_app: true}
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ntype}: {self.title}"

    @property
    def is_read(self):
        return self.read_at is not None

    def mark_as_read(self):
        if not self.is_read:
            self.read_at = timezone.now()
            self.save(update_fields=["read_at"])


class ElectionStatistics(models.Model):
    """Pre-calculated election statistics"""
    election = models.OneToOneField(Election, on_delete=models.CASCADE, related_name="statistics")
    total_registered_voters = models.PositiveIntegerField(default=0)
    total_votes_cast = models.PositiveIntegerField(default=0)
    total_votes_verified = models.PositiveIntegerField(default=0)
    voter_participation_rate = models.FloatField(default=0.0)  # Percentage
    by_constituency = models.JSONField(default=dict)  # {constituency_id: {votes, rate}}
    by_district = models.JSONField(default=dict)  # {district_id: {votes, rate}}
    updated_at = models.DateTimeField(auto_now=True)
    last_calculated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stats for {self.election.title}"

    def calculate_stats(self):
        """Recalculate all statistics"""
        from django.db.models import Count

        # Total voters for this election's constituencies
        self.total_registered_voters = VoterProfile.objects.filter(
            constituency__election=self.election,
            is_verified=True,
            email_verified=True,
        ).count()

        # Total verified votes
        self.total_votes_verified = VoteVerification.objects.filter(
            ballot__election=self.election,
            status=VoteVerification.Status.VERIFIED
        ).count()

        # Total cast votes (pending + verified + rejected)
        self.total_votes_cast = EncryptedBallot.objects.filter(
            election=self.election
        ).count()

        # Participation rate
        if self.total_registered_voters > 0:
            self.voter_participation_rate = (self.total_votes_cast / self.total_registered_voters) * 100
        else:
            self.voter_participation_rate = 0.0

        self.save()


class PasswordResetToken(models.Model):
    """Secure password reset tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token = models.CharField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Reset token for {self.user.email}"

    @property
    def is_valid(self):
        """Check if token is still valid and unused"""
        return (
            self.used_at is None and
            timezone.now() <= self.expires_at
        )

    def mark_as_used(self):
        """Mark token as used"""
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])


class LoginAttempt(models.Model):
    """Track login attempts for security"""
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    success = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempted_at"]
        indexes = [
            models.Index(fields=["email", "-attempted_at"]),
            models.Index(fields=["ip_address", "-attempted_at"]),
        ]

    def __str__(self):
        return f"Login {'SUCCESS' if self.success else 'FAILED'}: {self.email}"


class SuspiciousActivity(models.Model):
    """Log suspicious activities for fraud detection"""
    class ActivityType(models.TextChoices):
        MULTIPLE_LOGINS = "MULTIPLE_LOGINS", "Multiple logins from different IPs"
        RAPID_VOTING = "RAPID_VOTING", "Rapid vote casting"
        INVALID_AGE = "INVALID_AGE", "Invalid age verification"
        IMPOSSIBLE_LOCATION = "IMPOSSIBLE_LOCATION", "Impossible location change"
        ADMIN_BYPASS = "ADMIN_BYPASS", "Attempted admin bypass"
        DUPLICATE_VOTE = "DUPLICATE_VOTE", "Duplicate vote attempt"

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    atype = models.CharField(max_length=30, choices=ActivityType.choices)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True)
    metadata = models.JSONField(default=dict)
    severity = models.IntegerField(default=1)  # 1-5, 5 is highest
    reported_at = models.DateTimeField(auto_now_add=True)
    investigated = models.BooleanField(default=False)
    investigation_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-reported_at"]

    def __str__(self):
        return f"{self.atype} - Severity {self.severity}"


class CandidateManifesto(models.Model):
    """Candidate policy documents and manifesto"""
    candidate = models.OneToOneField(Candidate, on_delete=models.CASCADE, related_name="manifesto")
    title = models.CharField(max_length=200, default="Campaign Manifesto")
    content = models.TextField()
    pdf_file = models.FileField(upload_to="manifestos/", blank=True, null=True)
    key_promises = models.JSONField(default=list)  # ["Promise 1", "Promise 2", ...]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Manifesto: {self.candidate.full_name_en}"


class ElectionSurvey(models.Model):
    """Opinion polls during elections"""
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        CLOSED = "CLOSED", "Closed"

    title = models.CharField(max_length=200)
    description = models.TextField()
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="surveys")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="surveys_created")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    total_responses = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        now = timezone.now()
        return self.status == self.Status.ACTIVE and self.starts_at <= now <= self.ends_at


class SurveyQuestion(models.Model):
    """Survey questions"""
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = "MULTIPLE_CHOICE", "Multiple Choice"
        RATING = "RATING", "Rating (1-5)"
        TEXT = "TEXT", "Text Response"
        CANDIDATE_PREFERENCE = "CANDIDATE_PREFERENCE", "Candidate Preference"

    survey = models.ForeignKey(ElectionSurvey, on_delete=models.CASCADE, related_name="questions")
    question_text = models.CharField(max_length=500)
    qtype = models.CharField(max_length=30, choices=QuestionType.choices)
    options = models.JSONField(default=list)  # For multiple choice: ["Option 1", "Option 2", ...]
    order = models.PositiveIntegerField(default=0)
    required = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.question_text


class SurveyResponse(models.Model):
    """User survey responses"""
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="survey_responses")
    survey = models.ForeignKey(ElectionSurvey, on_delete=models.CASCADE, related_name="responses")
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, related_name="responses")
    answer = models.TextField()  # Text, rating, or selected option
    responded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["voter", "survey", "question"]

    def __str__(self):
        return f"Response to {self.survey.title}"


class VoterEducation(models.Model):
    """Educational content for voters"""
    class ContentType(models.TextChoices):
        TUTORIAL = "TUTORIAL", "Tutorial"
        FAQ = "FAQ", "FAQ"
        GUIDE = "GUIDE", "Guide"
        VIDEO = "VIDEO", "Video Lesson"
        ARTICLE = "ARTICLE", "Article"

    title = models.CharField(max_length=200)
    description = models.TextField()
    content = models.TextField()
    ctype = models.CharField(max_length=20, choices=ContentType.choices)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, null=True, blank=True, related_name="education")
    video_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name_plural = "Voter Education"

    def __str__(self):
        return self.title


class EducationProgress(models.Model):
    """Track voter education progress"""
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="education_progress")
    content = models.ForeignKey(VoterEducation, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.IntegerField(default=0)  # 0-100
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["voter", "content"]

    def __str__(self):
        return f"{self.voter.username} - {self.content.title}"


class CandidateEndorsement(models.Model):
    """Users can endorse candidates"""
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="endorsements")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="endorsements")
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    endorsed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["voter", "candidate", "election"]

    def __str__(self):
        return f"{self.voter.username} endorses {self.candidate.full_name_en}"


class ElectionAppeal(models.Model):
    """Dispute resolution and appeals"""
    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        RESOLVED = "RESOLVED", "Resolved"

    class AppealType(models.TextChoices):
        VOTER_ELIGIBILITY = "VOTER_ELIGIBILITY", "Voter Eligibility"
        VOTE_VERIFICATION = "VOTE_VERIFICATION", "Vote Verification"
        RESULTS = "RESULTS", "Results Dispute"
        CANDIDATE_DISPUTE = "CANDIDATE_DISPUTE", "Candidate Dispute"
        OTHER = "OTHER", "Other"

    appeal_id = models.CharField(max_length=50, unique=True)
    filing_voter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="appeals_filed")
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="appeals")
    atype = models.CharField(max_length=30, choices=AppealType.choices)
    description = models.TextField()
    supporting_documents = models.JSONField(default=list)  # File URLs
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="appeals_reviewed")
    review_notes = models.TextField(blank=True)
    filed_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-filed_at"]

    def __str__(self):
        return f"Appeal {self.appeal_id}"


class PartyPerformance(models.Model):
    """Track party performance across elections"""
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="performances")
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="party_performances")
    total_candidates = models.PositiveIntegerField(default=0)
    elected_candidates = models.PositiveIntegerField(default=0)
    total_votes = models.PositiveIntegerField(default=0)
    vote_share_percentage = models.FloatField(default=0.0)
    rank = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["party", "election"]

    def __str__(self):
        return f"{self.party.name_en} - {self.election.title}"


class VotingStatistics(models.Model):
    """Real-time voting analytics"""
    election = models.OneToOneField(Election, on_delete=models.CASCADE, related_name="voting_stats")
    total_eligible_voters = models.PositiveIntegerField(default=0)
    total_votes_cast = models.PositiveIntegerField(default=0)
    votes_by_gender = models.JSONField(default=dict)  # {male: count, female: count, other: count}
    votes_by_age_group = models.JSONField(default=dict)  # {"18-25": count, "26-35": count, ...}
    votes_by_time = models.JSONField(default=list)  # [{hour: time, votes: count}, ...]
    peak_voting_hour = models.IntegerField(null=True)  # 0-23
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stats: {self.election.title}"

    @property
    def participation_rate(self):
        if self.total_eligible_voters == 0:
            return 0
        return (self.total_votes_cast / self.total_eligible_voters) * 100


class DebatePost(models.Model):
    """Community discussion forum for debates"""
    topic = models.CharField(max_length=300)
    description = models.TextField()
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="debate_posts")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="debate_posts")
    category = models.CharField(max_length=50, default="general")  # general, policy, candidate, etc
    is_pinned = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    total_replies = models.PositiveIntegerField(default=0)
    total_views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-updated_at"]

    def __str__(self):
        return self.topic


class DebateComment(models.Model):
    """Replies to debate posts"""
    post = models.ForeignKey(DebatePost, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="debate_comments")
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment on {self.post.topic}"


class ComplianceReport(models.Model):
    """Generate compliance and audit reports"""
    class ReportType(models.TextChoices):
        AUDIT = "AUDIT", "Audit Report"
        COMPLIANCE = "COMPLIANCE", "Compliance Report"
        TRANSPARENCY = "TRANSPARENCY", "Transparency Report"
        SECURITY = "SECURITY", "Security Report"

    rtype = models.CharField(max_length=20, choices=ReportType.choices)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="compliance_reports")
    title = models.CharField(max_length=200)
    content = models.TextField()
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="reports_generated")
    generated_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to="compliance_reports/", blank=True, null=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.rtype}: {self.title}"