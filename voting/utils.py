# voting/utils.py - Utility functions for voting system

from __future__ import annotations

import os
import secrets
import string
from datetime import timedelta
from typing import Optional, Dict, Tuple

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.http import HttpRequest

import pyotp
import qrcode
from io import BytesIO
import base64

from .models import VoterProfile, PasswordResetToken, LoginAttempt, SuspiciousActivity, Notification


# ═══════════════════════════════════════════════════════════════
# OTP & Authentication Utilities
# ═══════════════════════════════════════════════════════════════

def generate_otp(length: int = 6) -> str:
    """Generate a random OTP code"""
    digits = string.digits
    return ''.join(secrets.choice(digits) for _ in range(length))


def send_otp_email(user: User, otp_code: str) -> bool:
    """Send OTP via email"""
    try:
        subject = "Your Voting System OTP"
        context = {
            'user': user,
            'otp_code': otp_code,
            'expires_in': getattr(settings, 'OTP_VALIDITY_MINUTES', 10),
        }
        html_message = render_to_string('auth/otp_email.html', context)

        send_mail(
            subject=subject,
            message=f"Your OTP is: {otp_code}",
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@voting.com'),
            recipient_list=[user.email],
            html_message=html_message,
        )
        return True
    except Exception as e:
        print(f"Failed to send OTP email to {user.email}: {e}")
        return False


def create_and_send_otp(user: User) -> Tuple[bool, str]:
    """Create OTP, save to profile, and send via email"""
    otp_code = generate_otp()

    try:
        vp = user.voter_profile
        vp.otp_code = otp_code
        vp.otp_expires_at = timezone.now() + timedelta(
            minutes=getattr(settings, 'OTP_VALIDITY_MINUTES', 10)
        )
        vp.save(update_fields=['otp_code', 'otp_expires_at'])

        success = send_otp_email(user, otp_code)
        return success, otp_code if not success else ""
    except Exception as e:
        return False, str(e)


def verify_otp(user: User, otp_code: str) -> Tuple[bool, str]:
    """Verify OTP code"""
    try:
        vp = user.voter_profile

        # Check if OTP exists
        if not vp.otp_code:
            return False, "No OTP found. Please request a new one."

        # Check if OTP has expired
        if timezone.now() > vp.otp_expires_at:
            vp.otp_code = ""
            vp.otp_expires_at = None
            vp.save(update_fields=['otp_code', 'otp_expires_at'])
            return False, "OTP has expired. Please request a new one."

        # Check if OTP matches
        if vp.otp_code != otp_code.strip():
            return False, "Invalid OTP code."

        # Mark email as verified
        vp.email_verified = True
        vp.otp_code = ""
        vp.otp_expires_at = None
        vp.save(update_fields=['email_verified', 'otp_code', 'otp_expires_at'])

        return True, "Email verified successfully!"
    except Exception as e:
        return False, str(e)


def generate_unique_voter_id(user: User) -> str:
    """Generate unique voter ID based on user"""
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"VP-{timestamp}-{random_part}"


# ═══════════════════════════════════════════════════════════════
# Password Reset Utilities
# ═══════════════════════════════════════════════════════════════

def generate_reset_token() -> str:
    """Generate a secure reset token"""
    return secrets.token_urlsafe(32)


def create_password_reset_token(user: User) -> str:
    """Create a password reset token for user"""
    token = generate_reset_token()
    expires_at = timezone.now() + timedelta(hours=24)

    PasswordResetToken.objects.create(
        user=user,
        token=token,
        expires_at=expires_at
    )
    return token


def send_password_reset_email(user: User, token: str) -> bool:
    """Send password reset link via email"""
    try:
        reset_link = f"{settings.SITE_URL}/auth/reset/{token}/"
        subject = "Reset Your Voting System Password"
        context = {
            'user': user,
            'reset_link': reset_link,
            'expires_in_hours': 24,
        }
        html_message = render_to_string('auth/password_reset_email.html', context)

        send_mail(
            subject=subject,
            message=f"Reset your password: {reset_link}",
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@voting.com'),
            recipient_list=[user.email],
            html_message=html_message,
        )
        return True
    except Exception as e:
        print(f"Failed to send password reset email to {user.email}: {e}")
        return False


def validate_reset_token(token: str) -> Optional[User]:
    """Validate reset token and return user if valid"""
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        if reset_token.is_valid:
            return reset_token.user
        return None
    except PasswordResetToken.DoesNotExist:
        return None


# ═══════════════════════════════════════════════════════════════
# Login & Security Utilities
# ═══════════════════════════════════════════════════════════════

def get_client_ip(request: HttpRequest) -> str:
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request: HttpRequest) -> str:
    """Get user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')[:1000]


def log_login_attempt(email: str, request: HttpRequest, success: bool) -> None:
    """Log login attempt to database"""
    try:
        LoginAttempt.objects.create(
            email=email.lower(),
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            success=success,
        )
    except Exception as e:
        print(f"Failed to log login attempt: {e}")


def check_login_rate_limit(email: str) -> Tuple[bool, str]:
    """Check if user has exceeded login attempt rate limit"""
    email = email.lower()

    try:
        vp = VoterProfile.objects.select_related('user').get(user__email=email)

        # Check if account is locked
        if vp.login_locked_until and timezone.now() < vp.login_locked_until:
            remaining = (vp.login_locked_until - timezone.now()).total_seconds()
            minutes = int(remaining / 60)
            return False, f"Account locked. Try again in {minutes} minutes."

        # Count failed attempts in last 15 minutes
        fifteen_ago = timezone.now() - timedelta(minutes=15)
        failed_attempts = LoginAttempt.objects.filter(
            email=email,
            success=False,
            attempted_at__gte=fifteen_ago
        ).count()

        max_attempts = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
        if failed_attempts >= max_attempts:
            # Lock account for 30 minutes
            vp.login_locked_until = timezone.now() + timedelta(minutes=30)
            vp.save(update_fields=['login_locked_until'])
            return False, "Too many failed attempts. Account locked for 30 minutes."

        return True, ""
    except VoterProfile.DoesNotExist:
        return True, ""
    except Exception as e:
        return True, ""  # Don't block on error


def reset_login_attempts(user: User) -> None:
    """Reset login attempts after successful login"""
    try:
        vp = user.voter_profile
        vp.login_attempts = 0
        vp.login_locked_until = None
        vp.save(update_fields=['login_attempts', 'login_locked_until'])
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# Age Verification Utilities
# ═══════════════════════════════════════════════════════════════

def get_age(date_of_birth) -> Optional[int]:
    """Calculate age from date of birth"""
    if not date_of_birth:
        return None
    from datetime import date
    today = date.today()
    return today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )


def verify_age(date_of_birth, min_age: int = 18) -> Tuple[bool, str]:
    """Verify if user is old enough to vote"""
    age = get_age(date_of_birth)
    if age is None:
        return False, "Date of birth not provided"
    if age < min_age:
        return False, f"Must be at least {min_age} years old. You are {age}."
    return True, ""


# ═══════════════════════════════════════════════════════════════
# Notification Utilities
# ═══════════════════════════════════════════════════════════════

def send_notification(
    user: User,
    ntype: str,
    title: str,
    message: str,
    election=None,
    send_email: bool = False,
    send_sms: bool = False,
) -> bool:
    """Create and send notification to user"""
    try:
        notification = Notification.objects.create(
            user=user,
            election=election,
            ntype=ntype,
            title=title,
            message=message,
            sent_via={
                'email': send_email,
                'sms': send_sms,
                'in_app': True,
            }
        )

        if send_email:
            send_notification_email(user, title, message)

        if send_sms:
            send_notification_sms(user, title, message)

        return True
    except Exception as e:
        print(f"Failed to send notification: {e}")
        return False


def send_notification_email(user: User, title: str, message: str) -> bool:
    """Send notification via email"""
    try:
        send_mail(
            subject=title,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@voting.com'),
            recipient_list=[user.email],
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_notification_sms(user: User, title: str, message: str) -> bool:
    """Send notification via SMS using Twilio"""
    try:
        from twilio.rest import Client

        account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')

        if not all([account_sid, auth_token, from_number]):
            return False

        vp = user.voter_profile
        if not vp.phone:
            return False

        client = Client(account_sid, auth_token)
        client.messages.create(
            body=f"{title}: {message}",
            from_=from_number,
            to=vp.phone,
        )
        return True
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# Suspicious Activity Detection
# ═══════════════════════════════════════════════════════════════

def detect_suspicious_activity(
    user: User,
    activity_type: str,
    description: str,
    ip_address: str,
    severity: int = 1,
    metadata: Dict = None,
) -> bool:
    """Log suspicious activity for review"""
    try:
        SuspiciousActivity.objects.create(
            user=user,
            atype=activity_type,
            description=description,
            ip_address=ip_address,
            severity=severity,
            metadata=metadata or {},
        )

        # If severity high, send alert to admins
        if severity >= 4:
            send_admin_alert(user, activity_type, description)

        return True
    except Exception as e:
        print(f"Failed to log suspicious activity: {e}")
        return False


def send_admin_alert(user: User, activity_type: str, description: str) -> None:
    """Send alert email to admin users"""
    try:
        from django.contrib.auth.models import User as DjangoUser
        admins = DjangoUser.objects.filter(is_staff=True)

        admin_emails = [admin.email for admin in admins if admin.email]

        if admin_emails:
            subject = f"⚠️ SECURITY ALERT: {activity_type}"
            message = f"User: {user.email}\nActivity: {description}"
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@voting.com'),
                recipient_list=admin_emails,
            )
    except Exception as e:
        print(f"Failed to send admin alert: {e}")


# ═══════════════════════════════════════════════════════════════
# Two-Factor Authentication Utilities
# ═══════════════════════════════════════════════════════════════

def setup_totp(user: User) -> Tuple[str, str]:
    """Setup TOTP (Time-based One-Time Password) for 2FA"""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name='Voting System'
    )

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    qr_code_base64 = base64.b64encode(img_io.getvalue()).decode()

    return secret, qr_code_base64


def verify_totp(secret: str, token: str) -> bool:
    """Verify TOTP token"""
    totp = pyotp.TOTP(secret)
    return totp.verify(token)

