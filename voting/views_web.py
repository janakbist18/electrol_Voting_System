from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404

from .forms import RegisterForm, VoterProfileForm
from .models import Election, Candidate, ResultTally
from .services import cast_vote, audit



def home(request):
    elections = Election.objects.order_by("-start_at")[:5]
    return render(request, "home.html", {"elections": elections})

def web_register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            audit(request, actor=user, action="REGISTER", object_type="User", object_id=user.id)
            messages.success(request, "Account created. Please log in.")
            return redirect("web_login")
    else:
        form = RegisterForm()
    return render(request, "auth/register.html", {"form": form})

def web_login(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").lower()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            audit(request, actor=user, action="LOGIN", object_type="User", object_id=user.id)
            return redirect("home")
        messages.error(request, "Invalid credentials.")
    return render(request, "auth/login.html")

def web_logout(request):
    if request.user.is_authenticated:
        audit(request, actor=request.user, action="LOGOUT", object_type="User", object_id=request.user.id)
    logout(request)
    return redirect("home")

@login_required
def voter_profile(request):
    vp = getattr(request.user, "voter_profile", None)
    if request.method == "POST":
        form = VoterProfileForm(request.POST, instance=vp)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            audit(request, actor=request.user, action="PROFILE_UPDATE", object_type="VoterProfile", object_id=obj.id)
            messages.success(request, "Profile saved. Admin must verify you before you can vote.")
            return redirect("voter_profile")
    else:
        form = VoterProfileForm(instance=vp)
    return render(request, "voter/profile.html", {"form": form, "vp": vp})

@login_required
def voter_vote(request, election_id: int):
    election = get_object_or_404(Election, pk=election_id)
    election.sync_status()

    vp = getattr(request.user, "voter_profile", None)
    if not vp or not vp.constituency_id:
        messages.error(request, "Set your constituency in Profile first.")
        return redirect("voter_profile")
    if not vp.is_verified:
        messages.error(request, "You are not verified yet. Ask admin to verify you.")
        return redirect("voter_profile")

    candidates = Candidate.objects.select_related("party").filter(
        constituency_id=vp.constituency_id,
        constituency__election_id=election.id
    ).order_by("party__abbreviation", "full_name_en")

    if request.method == "POST":
        candidate_id = int(request.POST.get("candidate_id") or 0)
        try:
            result = cast_vote(request=request, voter=request.user, election=election, candidate_id=candidate_id)
        except Exception as e:
            messages.error(request, str(e))
            return redirect("voter_vote", election_id=election.id)
        return render(request, "voter/receipt.html", {"receipt_uuid": result.receipt_uuid, "election": election})

    return render(request, "voter/vote.html", {"election": election, "candidates": candidates, "vp": vp})

def results_elections(request):
    elections = Election.objects.order_by("-start_at")
    return render(request, "results/elections.html", {"elections": elections})

def results_view(request, election_id: int):
    election = get_object_or_404(Election, pk=election_id)
    election.sync_status()

    if not election.has_ended:
        messages.error(request, "Results are not available yet.")
        return redirect("results_elections")

    constituency_id = request.GET.get("constituency")
    tallies = ResultTally.objects.select_related("candidate__party", "constituency").filter(election=election)
    if constituency_id:
        tallies = tallies.filter(constituency_id=constituency_id)

    tallies = tallies.order_by("-votes")
    constituencies = election.constituencies.order_by("code")

    return render(request, "results/results.html", {
        "election": election,
        "tallies": tallies,
        "constituencies": constituencies,
        "selected_constituency": constituency_id or "",
    })
def results(request):
    elections = Election.objects.order_by("-start_at")[:10]
    return render(request, "results/index.html", {"elections": elections})

def results_detail(request, election_id: int):
    election = get_object_or_404(Election, id=election_id)

    # Only show after ended
    if not election.has_ended:
        return render(request, "results/locked.html", {"election": election})

    tallies = (
        ResultTally.objects
        .filter(election=election)
        .select_related("candidate__party", "constituency")
        .order_by("constituency__code", "-votes")
    )

    return render(request, "results/detail.html", {
        "election": election,
        "tallies": tallies,
    })