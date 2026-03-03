from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from voting.models import Election, Constituency, Party, Candidate, VoterProfile, VoterParticipation, ResultTally
from voting.services import cast_vote

@pytest.mark.django_db
def seed_simple_election():
    now = timezone.now()
    e = Election.objects.create(
        title="Test Election",
        description="",
        start_at=now - timedelta(hours=1),
        end_at=now + timedelta(hours=1),
        status=Election.Status.RUNNING,
    )
    c1 = Constituency.objects.create(election=e, name="Kathmandu-1", code="KTM-1")
    p = Party.objects.create(name_en="Party", name_np="", abbreviation="P", symbol_text="")
    cand = Candidate.objects.create(full_name_en="Candidate", full_name_np="", party=p, constituency=c1)
    ResultTally.objects.get_or_create(election=e, constituency=c1, candidate=cand, defaults={"votes": 0})
    return e, c1, cand

@pytest.mark.django_db
def make_verified_voter(constituency):
    u = User.objects.create_user(username="v@example.com", email="v@example.com", password="StrongPass123!")
    vp = u.voter_profile
    vp.is_verified = True
    vp.constituency = constituency
    vp.save()
    return u

class DummyReq:
    META = {"REMOTE_ADDR": "127.0.0.1", "HTTP_USER_AGENT": "pytest"}

@pytest.mark.django_db
def test_unverified_voter_cannot_vote(settings):
    from cryptography.fernet import Fernet
    settings.FERNET_KEY = Fernet.generate_key().decode()

    e, cons, cand = seed_simple_election()
    u = User.objects.create_user(username="u@example.com", email="u@example.com", password="StrongPass123!")
    u.voter_profile.constituency = cons
    u.voter_profile.is_verified = False
    u.voter_profile.save()

    with pytest.raises(PermissionError):
        cast_vote(request=DummyReq(), voter=u, election=e, candidate_id=cand.id)

@pytest.mark.django_db
def test_voter_cannot_vote_twice(settings):
    from cryptography.fernet import Fernet
    settings.FERNET_KEY = Fernet.generate_key().decode()

    e, cons, cand = seed_simple_election()
    u = make_verified_voter(cons)

    cast_vote(request=DummyReq(), voter=u, election=e, candidate_id=cand.id)
    with pytest.raises(ValueError):
        cast_vote(request=DummyReq(), voter=u, election=e, candidate_id=cand.id)

@pytest.mark.django_db
def test_cannot_vote_outside_time_window(settings):
    from cryptography.fernet import Fernet
    settings.FERNET_KEY = Fernet.generate_key().decode()

    now = timezone.now()
    e = Election.objects.create(
        title="Closed Election",
        description="",
        start_at=now - timedelta(hours=3),
        end_at=now - timedelta(hours=2),
        status=Election.Status.ENDED,
    )
    cons = Constituency.objects.create(election=e, name="KTM-1", code="KTM-1")
    p = Party.objects.create(name_en="Party", name_np="", abbreviation="P2", symbol_text="")
    cand = Candidate.objects.create(full_name_en="Candidate", full_name_np="", party=p, constituency=cons)
    ResultTally.objects.get_or_create(election=e, constituency=cons, candidate=cand, defaults={"votes": 0})

    u = make_verified_voter(cons)
    with pytest.raises(ValueError):
        cast_vote(request=DummyReq(), voter=u, election=e, candidate_id=cand.id)

@pytest.mark.django_db
def test_results_hidden_before_end(client, settings):
    from cryptography.fernet import Fernet
    settings.FERNET_KEY = Fernet.generate_key().decode()

    e, cons, cand = seed_simple_election()
    resp = client.get(f"/api/elections/{e.id}/results")
    assert resp.status_code == 403

@pytest.mark.django_db
def test_tally_increments(settings):
    from cryptography.fernet import Fernet
    settings.FERNET_KEY = Fernet.generate_key().decode()

    e, cons, cand = seed_simple_election()
    u = make_verified_voter(cons)

    cast_vote(request=DummyReq(), voter=u, election=e, candidate_id=cand.id)
    t = ResultTally.objects.get(election=e, constituency=cons, candidate=cand)
    assert t.votes == 1