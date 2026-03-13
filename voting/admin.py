from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Election, District, Constituency, Party, Candidate,
    VoterProfile, VoterParticipation, EncryptedBallot, ResultTally, AuditLog, VoteVerification,
    CandidateMetadata, Notification, ElectionStatistics, PasswordResetToken,
    LoginAttempt, SuspiciousActivity, CandidateManifesto, ElectionSurvey, SurveyQuestion,
    SurveyResponse, VoterEducation, EducationProgress, CandidateEndorsement, ElectionAppeal,
    PartyPerformance, VotingStatistics, DebatePost, DebateComment, ComplianceReport
)
from .services import verify_vote

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

    fieldsets = (
        ("Basic Info", {"fields": ("full_name_en", "full_name_np", "party", "constituency")}),
        ("Media", {"fields": ("photo",)}),
    )
    readonly_fields = ("photo",)

# ✅ Auto-verify actions
@admin.action(description="✅ Verify selected voters")
def verify_voters(modeladmin, request, queryset):
    queryset.update(is_verified=True)

@admin.action(description="❌ Unverify selected voters")
def unverify_voters(modeladmin, request, queryset):
    queryset.update(is_verified=False)

@admin.register(VoterProfile)
class VoterProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "unique_voter_id", "is_verified", "email_verified", "is_admin", "age_display", "district")
    list_filter = ("is_verified", "email_verified", "is_admin", "district")
    search_fields = ("user__username", "user__email", "citizenship_id", "phone", "unique_voter_id")
    actions = [verify_voters, unverify_voters]
    readonly_fields = ("unique_voter_id", "created_at", "updated_at", "last_login_at", "last_login_ip")

    # nicer edit page
    fieldsets = (
        ("Account", {"fields": ("user", "is_verified", "email_verified", "is_admin")}),
        ("Identity", {
            "fields": ("unique_voter_id", "citizenship_id", "phone", "date_of_birth", "profile_photo")
        }),
        ("Location", {"fields": ("district", "constituency")}),
        ("Security", {
            "fields": ("otp_code", "otp_expires_at", "google_oauth_id", "last_login_ip", "last_login_at", "login_attempts", "login_locked_until"),
            "classes": ("collapse",)
        }),
        ("Metadata", {
            "fields": ("metadata",),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def age_display(self, obj):
        if obj.age:
            return f"{obj.age} years"
        return "Not set"
    age_display.short_description = "Age"

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


# ✅ Vote Verification Actions
@admin.action(description="✅ Approve selected votes")
def approve_votes(modeladmin, request, queryset):
    for vote_verification in queryset.filter(status=VoteVerification.Status.PENDING):
        verify_vote(admin_user=request.user, vote_verification=vote_verification, approved=True)

@admin.action(description="❌ Reject selected votes")
def reject_votes(modeladmin, request, queryset):
    for vote_verification in queryset.filter(status=VoteVerification.Status.PENDING):
        verify_vote(admin_user=request.user, vote_verification=vote_verification, approved=False)

@admin.register(VoteVerification)
class VoteVerificationAdmin(admin.ModelAdmin):
    list_display = ("id", "voter", "status", "created_at", "verified_by", "verified_at")
    list_filter = ("status", "created_at")
    search_fields = ("voter__username", "voter__email")
    readonly_fields = ("ballot", "voter", "created_at", "verified_by", "verified_at")
    actions = [approve_votes, reject_votes]

    fieldsets = (
        ("Vote Info", {"fields": ("ballot", "voter", "created_at")}),
        ("Verification", {"fields": ("status", "verified_by", "verified_at", "notes")}),
    )

    def get_queryset(self, request):
        # Show pending votes first
        qs = super().get_queryset(request)
        return qs.order_by("-created_at")


# ═══════════════════════════════════════════════════════════════
# NEW ADMIN CLASSES - Enhanced Features
# ═══════════════════════════════════════════════════════════════

@admin.register(CandidateMetadata)
class CandidateMetadataAdmin(admin.ModelAdmin):
    list_display = ("candidate", "contact_email", "website")
    search_fields = ("candidate__full_name_en", "contact_email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "ntype", "title", "is_read_status", "sent_at")
    list_filter = ("ntype", "sent_at", "read_at")
    search_fields = ("user__email", "title", "message")
    readonly_fields = ("sent_at", "created_at")

    def is_read_status(self, obj):
        if obj.is_read:
            return format_html('<span style="color: green;">✓ Read</span>')
        return format_html('<span style="color: red;">✗ Unread</span>')
    is_read_status.short_description = "Status"


@admin.register(ElectionStatistics)
class ElectionStatisticsAdmin(admin.ModelAdmin):
    list_display = ("election", "total_registered_voters", "total_votes_cast", "voter_participation_rate")
    readonly_fields = ("election", "updated_at", "last_calculated_at")
    fields = ("election", "total_registered_voters", "total_votes_cast", "total_votes_verified",
              "voter_participation_rate", "updated_at", "last_calculated_at")


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "is_valid_status", "created_at", "expires_at", "used_at")
    list_filter = ("created_at", "used_at")
    search_fields = ("user__email", "token")
    readonly_fields = ("token", "created_at", "expires_at")

    def is_valid_status(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Invalid/Used</span>')
    is_valid_status.short_description = "Status"


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ("email", "ip_address", "success_status", "attempted_at")
    list_filter = ("success", "attempted_at")
    search_fields = ("email", "ip_address")
    readonly_fields = ("email", "ip_address", "user_agent", "attempted_at")

    def success_status(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓ Success</span>')
        return format_html('<span style="color: red;">✗ Failed</span>')
    success_status.short_description = "Result"


@admin.register(SuspiciousActivity)
class SuspiciousActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "atype", "severity_badge", "investigated_status", "reported_at")
    list_filter = ("atype", "severity", "investigated", "reported_at")
    search_fields = ("user__email", "description", "ip_address")
    readonly_fields = ("reported_at",)

    fieldsets = (
        ("Activity Info", {"fields": ("user", "atype", "description", "severity")}),
        ("Technical", {"fields": ("ip_address", "metadata")}),
        ("Investigation", {"fields": ("investigated", "investigation_notes")}),
        ("Timestamp", {"fields": ("reported_at",)}),
    )

    def severity_badge(self, obj):
        colors = {1: "gray", 2: "blue", 3: "orange", 4: "red", 5: "darkred"}
        color = colors.get(obj.severity, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">Severity {}</span>',
            color, obj.severity
        )
    severity_badge.short_description = "Severity"

    def investigated_status(self, obj):
        if obj.investigated:
            return format_html('<span style="color: green;">✓ Investigated</span>')
        return format_html('<span style="color: orange;">⚠ Pending</span>')
    investigated_status.short_description = "Investigation"


# ═══════════════════════════════════════════════════════════════
# ADVANCED FEATURES ADMIN
# ═══════════════════════════════════════════════════════════════

@admin.register(CandidateManifesto)
class CandidateManifestoAdmin(admin.ModelAdmin):
    list_display = ("candidate", "title", "created_at", "updated_at")
    search_fields = ("candidate__full_name_en", "title")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Candidate", {"fields": ("candidate",)}),
        ("Manifesto", {"fields": ("title", "content", "key_promises", "pdf_file")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(ElectionSurvey)
class ElectionSurveyAdmin(admin.ModelAdmin):
    list_display = ("title", "election", "status", "total_responses", "starts_at", "ends_at")
    list_filter = ("status", "election", "starts_at")
    search_fields = ("title", "description")
    readonly_fields = ("total_responses", "created_at")
    fieldsets = (
        ("Basic Info", {"fields": ("title", "description", "election", "created_by")}),
        ("Schedule", {"fields": ("starts_at", "ends_at", "status")}),
        ("Stats", {"fields": ("total_responses", "created_at")}),
    )


class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion
    extra = 1
    fields = ("question_text", "qtype", "options", "order", "required")


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ("survey", "question_text", "qtype", "order")
    list_filter = ("qtype", "survey__election")
    search_fields = ("question_text", "survey__title")


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ("survey", "voter", "question", "responded_at")
    list_filter = ("survey__election", "responded_at")
    search_fields = ("voter__email", "survey__title")
    readonly_fields = ("voter", "survey", "question", "responded_at")


@admin.register(VoterEducation)
class VoterEducationAdmin(admin.ModelAdmin):
    list_display = ("title", "ctype", "election", "is_published", "order")
    list_filter = ("ctype", "is_published", "election")
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Content", {"fields": ("title", "description", "content", "ctype", "video_url")}),
        ("Settings", {"fields": ("election", "is_published", "order")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(EducationProgress)
class EducationProgressAdmin(admin.ModelAdmin):
    list_display = ("voter", "content", "progress_percentage", "is_completed", "started_at")
    list_filter = ("completed_at", "started_at")
    search_fields = ("voter__email", "content__title")
    readonly_fields = ("started_at", "content", "voter")

    def is_completed(self, obj):
        if obj.completed_at:
            return format_html('<span style="color: green;">✓ Completed</span>')
        return format_html('<span style="color: orange;">In Progress</span>')
    is_completed.short_description = "Status"


@admin.register(CandidateEndorsement)
class CandidateEndorsementAdmin(admin.ModelAdmin):
    list_display = ("voter", "candidate", "election", "endorsed_at")
    list_filter = ("election", "endorsed_at")
    search_fields = ("voter__email", "candidate__full_name_en")
    readonly_fields = ("endorsed_at",)


@admin.register(ElectionAppeal)
class ElectionAppealAdmin(admin.ModelAdmin):
    list_display = ("appeal_id", "atype", "status", "filed_at", "resolved_at")
    list_filter = ("atype", "status", "election", "filed_at")
    search_fields = ("appeal_id", "filing_voter__email", "description")
    readonly_fields = ("appeal_id", "filed_at", "resolved_at")
    fieldsets = (
        ("Appeal Info", {"fields": ("appeal_id", "filing_voter", "election", "atype")}),
        ("Description", {"fields": ("description", "supporting_documents")}),
        ("Review", {"fields": ("status", "reviewed_by", "review_notes")}),
        ("Timestamps", {"fields": ("filed_at", "resolved_at")}),
    )


@admin.register(PartyPerformance)
class PartyPerformanceAdmin(admin.ModelAdmin):
    list_display = ("party", "election", "total_candidates", "elected_candidates", "vote_share_badge", "rank")
    list_filter = ("party", "election")
    search_fields = ("party__name_en", "election__title")
    readonly_fields = ("updated_at",)

    def vote_share_badge(self, obj):
        return format_html(
            '<span style="color: darkgreen; font-weight: bold;">{:.1f}%</span>',
            obj.vote_share_percentage
        )
    vote_share_badge.short_description = "Vote Share"


@admin.register(VotingStatistics)
class VotingStatisticsAdmin(admin.ModelAdmin):
    list_display = ("election", "total_eligible_voters", "total_votes_cast", "participation_rate_badge", "peak_voting_hour")
    readonly_fields = ("election", "votes_by_gender", "votes_by_age_group", "votes_by_time", "last_updated")
    fieldsets = (
        ("Election", {"fields": ("election",)}),
        ("Voting Stats", {"fields": ("total_eligible_voters", "total_votes_cast")}),
        ("Demographics", {"fields": ("votes_by_gender", "votes_by_age_group")}),
        ("Timing", {"fields": ("votes_by_time", "peak_voting_hour")}),
        ("Updated", {"fields": ("last_updated",)}),
    )

    def participation_rate_badge(self, obj):
        rate = obj.participation_rate
        return format_html(
            '<span style="color: darkblue; font-weight: bold;">{:.1f}%</span>',
            rate
        )
    participation_rate_badge.short_description = "Participation Rate"


@admin.register(DebatePost)
class DebatePostAdmin(admin.ModelAdmin):
    list_display = ("topic", "election", "created_by", "is_pinned_on", "is_approved_status", "total_replies", "created_at")
    list_filter = ("is_pinned", "is_approved", "election", "category", "created_at")
    search_fields = ("topic", "description", "created_by__email")
    readonly_fields = ("total_replies", "total_views", "created_at", "updated_at")

    def is_pinned_on(self, obj):
        if obj.is_pinned:
            return format_html('<span style="color: red;">📌 Pinned</span>')
        return "—"
    is_pinned_on.short_description = "Pinned"

    def is_approved_status(self, obj):
        if obj.is_approved:
            return format_html('<span style="color: green;">✓ Approved</span>')
        return format_html('<span style="color: orange;">⚠ Pending</span>')
    is_approved_status.short_description = "Approval"


@admin.register(DebateComment)
class DebateCommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "is_approved_status", "likes", "dislikes", "created_at")
    list_filter = ("is_approved", "created_at", "post__election")
    search_fields = ("author__email", "content", "post__topic")
    readonly_fields = ("likes", "dislikes", "created_at", "updated_at")

    def is_approved_status(self, obj):
        if obj.is_approved:
            return format_html('<span style="color: green;">✓ Approved</span>')
        return format_html('<span style="color: orange;">⚠ Pending</span>')
    is_approved_status.short_description = "Approval"


@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display = ("rtype", "election", "title", "generated_by", "is_published_status", "generated_at")
    list_filter = ("rtype", "election", "is_published", "generated_at")
    search_fields = ("title", "content", "generated_by__email")
    readonly_fields = ("generated_at",)
    fieldsets = (
        ("Report Info", {"fields": ("rtype", "election", "title", "generated_by")}),
        ("Content", {"fields": ("content", "pdf_file")}),
        ("Publishing", {"fields": ("is_published",)}),
        ("Generated", {"fields": ("generated_at",)}),
    )

    def is_published_status(self, obj):
        if obj.is_published:
            return format_html('<span style="color: green;">✓ Published</span>')
        return format_html('<span style="color: gray;">Draft</span>')
    is_published_status.short_description = "Status"