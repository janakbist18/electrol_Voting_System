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

    constituency = models.ForeignKey(
        Constituency,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="voter_profiles",
    )

    def __str__(self):
        return f"VoterProfile({self.user.username})"


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