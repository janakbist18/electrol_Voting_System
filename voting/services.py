from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from nepal_voting.utils_crypto import CryptoBox
from .models import (
    AuditLog,
    Candidate,
    Election,
    EncryptedBallot,
    ResultTally,
    VoterParticipation,
)


def _get_crypto() -> CryptoBox:
    key = getattr(settings, "FERNET_KEY", None)
    if not key:
        raise RuntimeError("FERNET_KEY missing. Put it in .env (see .env.example).")
    return CryptoBox(Fernet(key.encode("utf-8")))


def audit(
    request,
    *,
    actor,
    action: str,
    object_type: str,
    object_id: str = "",
    meta: Optional[dict] = None,
):
    meta = meta or {}
    ip = request.META.get("REMOTE_ADDR")
    ua = request.META.get("HTTP_USER_AGENT", "")[:1000]
    AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        meta_json=meta,
        ip=ip,
        ua=ua,
    )


@dataclass(frozen=True)
class VoteResult:
    receipt_uuid: str


@transaction.atomic
def cast_vote(*, request, voter, election: Election, candidate_id: int) -> VoteResult:
    election.sync_status()

    now = timezone.now()
    if not (election.status == Election.Status.RUNNING and election.start_at <= now <= election.end_at):
        audit(request, actor=voter, action="VOTE_REJECTED_TIME", object_type="Election", object_id=election.id)
        raise ValueError("Election is not accepting votes at this time.")

    vp = getattr(voter, "voter_profile", None)
    if not vp or not vp.is_verified or not vp.constituency_id:
        audit(request, actor=voter, action="VOTE_REJECTED_UNVERIFIED", object_type="User", object_id=voter.id)
        raise PermissionError("Voter is not verified or has no constituency set.")

    candidate = (
        Candidate.objects.select_related("constituency", "party")
        .filter(
            id=candidate_id,
            constituency_id=vp.constituency_id,
            constituency__election_id=election.id,
        )
        .first()
    )
    if not candidate:
        audit(request, actor=voter, action="VOTE_REJECTED_BAD_CANDIDATE", object_type="Election", object_id=election.id)
        raise ValueError("Invalid candidate for this election/constituency.")

    participation, _ = VoterParticipation.objects.select_for_update().get_or_create(
        voter=voter,
        election=election,
        defaults={"has_voted": False},
    )
    if participation.has_voted:
        audit(request, actor=voter, action="VOTE_REJECTED_DUPLICATE", object_type="Election", object_id=election.id)
        raise ValueError("You have already voted in this election.")

    # Create ballot first -> receipt_uuid comes from DB field
    ballot = EncryptedBallot.objects.create(
        election=election,
        constituency_id=vp.constituency_id,
        encrypted_payload="",  # temporary
    )

    receipt_uuid = str(ballot.receipt_uuid)

    payload = {
        "election_id": election.id,
        "constituency_id": vp.constituency_id,
        "candidate_id": candidate.id,
        "server_timestamp": now.isoformat(),
        "receipt_uuid": receipt_uuid,
    }
    crypto = _get_crypto()
    encrypted_payload = crypto.encrypt_text(json.dumps(payload, separators=(",", ":"), sort_keys=True))

    ballot.encrypted_payload = encrypted_payload
    ballot.save(update_fields=["encrypted_payload"])

    participation.has_voted = True
    participation.voted_at = now
    participation.save(update_fields=["has_voted", "voted_at"])

    tally, _ = ResultTally.objects.select_for_update().get_or_create(
        election=election,
        constituency_id=vp.constituency_id,
        candidate=candidate,
        defaults={"votes": 0},
    )
    ResultTally.objects.filter(pk=tally.pk).update(votes=F("votes") + 1)

    audit(
        request,
        actor=voter,
        action="VOTE_CAST",
        object_type="Election",
        object_id=election.id,
        meta={"receipt_uuid": receipt_uuid, "constituency_id": vp.constituency_id},
    )

    return VoteResult(receipt_uuid=receipt_uuid)