from __future__ import annotations

from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Election, Candidate, ResultTally
from .permissions import IsVerifiedVoter
from .serializers import (
    RegisterSerializer,
    ElectionSerializer,
    CandidateSerializer,
    VoteSerializer,
)
from .services import cast_vote

@api_view(["POST"])
@permission_classes([AllowAny])
def api_register(request):
    ser = RegisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user = ser.save()
    return Response({"id": user.id, "email": user.email}, status=status.HTTP_201_CREATED)

@api_view(["POST"])
@permission_classes([AllowAny])
def api_login(request):
    email = (request.data.get("email") or "").lower()
    password = request.data.get("password") or ""
    user = authenticate(request, username=email, password=password)
    if not user:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
    login(request, user)
    return Response({"detail": "Logged in"})

@api_view(["GET"])
@permission_classes([AllowAny])
def api_elections(request):
    qs = Election.objects.order_by("-start_at")
    return Response(ElectionSerializer(qs, many=True).data)

@api_view(["GET"])
@permission_classes([AllowAny])
def api_candidates(request, election_id: int):
    election = get_object_or_404(Election, pk=election_id)
    constituency_id = request.query_params.get("constituency")
    qs = Candidate.objects.select_related("party", "constituency").filter(constituency__election=election)
    if constituency_id:
        qs = qs.filter(constituency_id=constituency_id)
    return Response(CandidateSerializer(qs, many=True).data)

@api_view(["POST"])
@permission_classes([IsVerifiedVoter])
def api_vote(request, election_id: int):
    election = get_object_or_404(Election, pk=election_id)
    ser = VoteSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    try:
        result = cast_vote(
            request=request,
            voter=request.user,
            election=election,
            candidate_id=ser.validated_data["candidate_id"],
        )
    except PermissionError as e:
        return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"receipt_uuid": result.receipt_uuid}, status=status.HTTP_201_CREATED)

@api_view(["GET"])
@permission_classes([AllowAny])
def api_results(request, election_id: int):
    election = get_object_or_404(Election, pk=election_id)
    election.sync_status()

    if not election.has_ended:
        return Response({"detail": "Results are not available yet."}, status=status.HTTP_403_FORBIDDEN)

    constituency_id = request.query_params.get("constituency")
    tallies = ResultTally.objects.select_related("candidate__party").filter(election=election)
    if constituency_id:
        tallies = tallies.filter(constituency_id=constituency_id)

    rows = []
    for t in tallies.order_by("-votes"):
        rows.append({
            "candidate_id": t.candidate_id,
            "candidate_name": t.candidate.full_name_en,
            "party": t.candidate.party.abbreviation,
            "votes": t.votes,
        })

    return Response({
        "election_id": election.id,
        "constituency_id": int(constituency_id) if constituency_id else None,
        "rows": rows,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def api_vote_status(request):
    """Check the status of user's votes across all elections"""
    if not request.user.is_authenticated:
        return Response(
            {"detail": "Must be logged in to check vote status"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    from .models import VoteVerification

    votes = VoteVerification.objects.filter(
        voter=request.user
    ).select_related("ballot__election", "ballot__constituency").order_by("-created_at")

    vote_statuses = []
    for v in votes:
        vote_statuses.append({
            "election_id": v.ballot.election.id,
            "election_title": v.ballot.election.title,
            "status": v.status,
            "receipt_uuid": str(v.ballot.receipt_uuid),
            "voted_at": v.created_at.isoformat(),
            "verified_at": v.verified_at.isoformat() if v.verified_at else None,
        })

    return Response({
        "user_email": request.user.email,
        "votes": vote_statuses,
    })