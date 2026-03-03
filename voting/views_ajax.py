from __future__ import annotations
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from .models import Constituency

@login_required
def constituencies_by_district(request):
    district_id = request.GET.get("district_id")
    election_id = request.GET.get("election_id")

    qs = Constituency.objects.all()
    if district_id:
        qs = qs.filter(district_id=district_id)
    if election_id:
        qs = qs.filter(election_id=election_id)

    data = [{"id": c.id, "text": f"{c.code} - {c.name}"} for c in qs.order_by("code")]
    return JsonResponse({"results": data})

@require_GET
def constituencies_by_district(request):
    district_id = request.GET.get("district_id")
    if not district_id:
        return JsonResponse({"results": []})

    qs = Constituency.objects.filter(district_id=district_id).order_by("code")
    data = [{"id": c.id, "text": str(c)} for c in qs]
    return JsonResponse({"results": data})