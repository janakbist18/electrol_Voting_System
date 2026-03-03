from django.contrib import admin
from django.utils import timezone

from .models import (
    Election, District, Constituency, Party, Candidate,
    VoterProfile, VoterParticipation, EncryptedBallot, ResultTally, AuditLog
)

@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "start_at", "end_at")
    list_filter = ("status",)
    search_fields = ("title",)

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    search_fields = ("name_en", "name_np")

@admin.register(Constituency)
class ConstituencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "district", "election")
    list_filter = ("election", "district")
    search_fields = ("code", "name", "district__name_en")

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ("abbreviation", "name_en", "name_np")
    search_fields = ("abbreviation", "name_en", "name_np")

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("full_name_en", "party", "constituency")
    list_filter = ("party", "constituency__district", "constituency__election")
    search_fields = ("full_name_en", "full_name_np", "party__abbreviation", "constituency__code")

# ✅ Auto-verify actions
@admin.action(description="✅ Verify selected voters")
def verify_voters(modeladmin, request, queryset):
    queryset.update(is_verified=True)

@admin.action(description="❌ Unverify selected voters")
def unverify_voters(modeladmin, request, queryset):
    queryset.update(is_verified=False)

@admin.register(VoterProfile)
class VoterProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_verified", "citizenship_id", "phone", "district", "constituency")
    list_filter = ("is_verified", "district")
    search_fields = ("user__username", "user__email", "citizenship_id", "phone")
    actions = [verify_voters, unverify_voters]

    # nicer edit page
    fieldsets = (
        ("Account", {"fields": ("user", "is_verified")}),
        ("Identity", {"fields": ("citizenship_id", "phone")}),
        ("Location", {"fields": ("district", "constituency")}),
    )

@admin.register(VoterParticipation)
class VoterParticipationAdmin(admin.ModelAdmin):
    list_display = ("voter", "election", "has_voted", "voted_at")
    list_filter = ("has_voted", "election")
    search_fields = ("voter__username", "election__title")

@admin.register(EncryptedBallot)
class EncryptedBallotAdmin(admin.ModelAdmin):
    # do NOT show decrypted data
    list_display = ("election", "constituency", "created_at")
    list_filter = ("election", "constituency__district")
    readonly_fields = ("encrypted_payload", "created_at")

@admin.register(ResultTally)
class ResultTallyAdmin(admin.ModelAdmin):
    list_display = ("election", "constituency", "candidate", "votes")
    list_filter = ("election", "constituency__district")
    search_fields = ("candidate__full_name_en", "candidate__party__abbreviation", "constituency__code")

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "object_type", "object_id")
    list_filter = ("action", "object_type")
    search_fields = ("actor__username", "action", "object_type", "object_id")
    readonly_fields = ("created_at", "prev_hash", "hash", "meta_json", "ip", "ua")