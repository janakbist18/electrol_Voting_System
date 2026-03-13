# Advanced Features - Usage Guide

This guide explains how to use all the advanced features in the Nepal Voting System.

---

## Table of Contents

1. [Candidate Manifestos](#candidate-manifestos)
2. [Election Surveys](#election-surveys)
3. [Voter Education](#voter-education)
4. [Candidate Endorsements](#candidate-endorsements)
5. [Election Appeals](#election-appeals)
6. [Party Performance](#party-performance)
7. [Voting Statistics](#voting-statistics)
8. [Debate Forum](#debate-forum)
9. [Compliance Reports](#compliance-reports)

---

## Candidate Manifestos

### Setting Up Manifestos

**Step 1: Create Manifesto in Admin**

```
Admin → Candidates → [Select Candidate] → Add Manifesto
```

**Step 2: Fill Manifesto Details**

```
Title: "Campaign Manifesto 2026"
Biography: "Detailed background..."
Achievements: "Previous accomplishments..."
Policies: "Policy positions on key issues..."
Contact Email: "candidate@example.com"
Website: "https://candidate-website.com"
PDF File: [Upload manifesto PDF]
Key Promises: ["Promise 1", "Promise 2", "Promise 3"]
Social Media: {"twitter": "@handle", "facebook": "page"}
```

**Step 3: Display in Voter Interface**

```python
# In views.py
candidate = Candidate.objects.get(id=candidate_id)
context['manifesto'] = candidate.manifesto
```

**Step 4: Display Manifesto**

```html
<!-- Template -->
{% if manifesto %}
<h3>{{ manifesto.title }}</h3>
<p>{{ manifesto.biography }}</p>
<div class="policies">{{ manifesto.policies|safe }}</div>
{% if manifesto.pdf_file %}
<a href="{{ manifesto.pdf_file.url }}" class="btn">Download PDF</a>
{% endif %}
<ul class="promises">
  {% for promise in manifesto.key_promises %}
  <li>{{ promise }}</li>
  {% endfor %}
</ul>
{% endif %}
```

### API Endpoint

```python
# GET /api/candidates/{id}/manifesto/
{
    "candidate_id": 1,
    "biography": "...",
    "achievements": "...",
    "policies": "...",
    "key_promises": ["Promise 1", "Promise 2"],
    "website": "https://...",
    "social_media": {"twitter": "@...", "facebook": "..."}
}
```

---

## Election Surveys

### Creating Surveys

**Step 1: Create Survey in Admin**

```
Admin → Election Surveys → Add Survey
```

**Step 2: Configure Survey**

```
Title: "Exit Poll 2026"
Description: "Post-voting opinion survey"
Election: [Select election]
Status: DRAFT (then ACTIVE later)
Starts At: 2026-04-01 08:00
Ends At: 2026-04-01 17:00
```

**Step 3: Add Survey Questions**

```
Admin → Survey Questions → Add Questions
```

**Question Types:**

```python
# Multiple Choice
Q: "Who would you vote for?"
Options: ["Candidate A", "Candidate B", "Candidate C"]

# Rating Scale
Q: "How satisfied are you with the election process?"
Type: RATING (1-5)

# Text Response
Q: "What improvements do you suggest?"
Type: TEXT

# Candidate Preference
Q: "Which candidate would you prefer as PM?"
Type: CANDIDATE_PREFERENCE
```

**Step 4: Activate Survey**

```
Edit Survey → Status: ACTIVE
```

### Collect Responses

**Python/Django**

```python
from voting.models import SurveyResponse

# Save response
response = SurveyResponse.objects.create(
    voter=request.user,
    survey=survey,
    question=question,
    answer="Candidate A"
)

# Get all responses
responses = SurveyResponse.objects.filter(survey=survey)
```

### Analyze Results

**Survey Statistics**

```python
from django.db.models import Count

survey = ElectionSurvey.objects.get(id=survey_id)
stats = {
    'total_responses': survey.total_responses,
    'completion_rate': (survey.total_responses / eligible_voters) * 100,
}

# Response by question
for question in survey.questions.all():
    answers = question.responses.values('answer').annotate(
        count=Count('id')
    ).order_by('-count')
    print(f"{question.question_text}: {answers}")
```

### API Endpoints

```python
# Get surveys
GET /api/elections/{election_id}/surveys/
→ [{id, title, status, total_responses}, ...]

# Submit response
POST /api/surveys/{survey_id}/respond/
{
    "question_id": 1,
    "answer": "Candidate A"
}

# Get survey results
GET /api/surveys/{survey_id}/results/
→ {results: [{question, answers: {option: count}}]}
```

---

## Voter Education

### Creating Educational Content

**Step 1: Create Content in Admin**

```
Admin → Voter Education → Add Content
```

**Step 2: Configure Content**

```
Title: "How to Register as a Voter"
Type: TUTORIAL (or FAQ, GUIDE, VIDEO, ARTICLE)
Content: "Step-by-step instructions..."
Election: [Optional - select if election-specific]
Video URL: "https://youtube.com/..." (for VIDEO type)
Order: 1 (display order)
Is Published: True
```

### Content Types

```python
# TUTORIAL - Step-by-step guide
"1. Visit the registration page
2. Fill in your email
3. Verify with OTP
4. Complete your profile"

# FAQ - Question & answer format
"Q: How do I register?
A: Use the registration form..."

# GUIDE - Comprehensive resource
"Complete guide to voting including
all requirements, process, and FAQs"

# VIDEO - YouTube embed
"Video URL for visual learning"

# ARTICLE - Blog post format
"News or informational article"
```

### Track Learning Progress

**In Views**

```python
from voting.models import EducationProgress, VoterEducation

# Get voter's progress
progress = EducationProgress.objects.filter(
    voter=request.user
)

# Display progress
context['total_content'] = VoterEducation.objects.filter(
    is_published=True
).count()
context['completed'] = progress.filter(
    completed_at__isnull=False
).count()
context['completion_rate'] = (
    context['completed'] / context['total_content'] * 100
)
```

**Mark Content as Complete**

```python
progress = EducationProgress.objects.get(
    voter=voter,
    content=content
)
progress.completed_at = timezone.now()
progress.progress_percentage = 100
progress.save()
```

### Display in Voter Dashboard

```html
<!-- education_dashboard.html -->
<div class="education-center">
  <h2>Voter Education</h2>
  <div class="progress-bar">
    <div class="progress" style="width: {{ completion_rate }}%"></div>
  </div>
  <p>{{ completed }} of {{ total_content }} completed</p>

  <div class="content-list">
    {% for content in education_content %}
    <div class="content-card">
      <h3>{{ content.title }}</h3>
      <p>{{ content.description }}</p>
      <a href="{% url 'view_content' content.id %}"> Learn More → </a>
    </div>
    {% endfor %}
  </div>
</div>
```

---

## Candidate Endorsements

### Enable Endorsements

**Step 1: Add to Voter Interface**

```html
<!-- candidate_detail.html -->
<button class="btn btn-primary" onclick="endorseCandidate({{ candidate.id }})">
  👍 Endorse Candidate
</button>
<p class="endorsement-count">{{ candidate.endorsements.count }} Endorsements</p>
```

**Step 2: Handle Endorsement**

```python
# views.py
from voting.models import CandidateEndorsement

@login_required
def endorse_candidate(request, candidate_id):
    candidate = Candidate.objects.get(id=candidate_id)
    election = request.GET.get('election')

    endorsement, created = CandidateEndorsement.objects.get_or_create(
        voter=request.user,
        candidate=candidate,
        election_id=election
    )

    return JsonResponse({
        'success': True,
        'endorsement_count': candidate.endorsements.count()
    })
```

### Display Endorsement Metrics

```python
# In candidate list view
candidates = Candidate.objects.annotate(
    endorsement_count=Count('endorsements')
).order_by('-endorsement_count')

context['candidates'] = candidates
```

**Template**

```html
<div class="candidate-card">
  <h3>{{ candidate.full_name_en }}</h3>
  <p>{{ candidate.party.name_en }}</p>
  <div class="metrics">
    <span class="endorsements">👍 {{ candidate.endorsement_count }}</span>
  </div>
</div>
```

### Create Endorsement Leaderboard

```python
# views.py
def endorsement_leaderboard(request, election_id):
    candidates = Candidate.objects.filter(
        constituency__election_id=election_id
    ).annotate(
        endorsement_count=Count('endorsements')
    ).order_by('-endorsement_count')[:10]

    return render(request, 'leaderboard.html', {
        'candidates': candidates
    })
```

---

## Election Appeals

### File an Appeal

**Step 1: Create Appeal Form**

```python
# forms.py
from django import forms
from voting.models import ElectionAppeal

class AppealForm(forms.ModelForm):
    class Meta:
        model = ElectionAppeal
        fields = ['atype', 'description', 'supporting_documents']
        widgets = {
            'atype': forms.Select(),
            'description': forms.Textarea(),
            'supporting_documents': forms.JSONField()
        }
```

**Step 2: Handle Appeal Submission**

```python
# views.py
import uuid

@login_required
def file_appeal(request, election_id):
    election = Election.objects.get(id=election_id)

    if request.method == 'POST':
        form = AppealForm(request.POST, request.FILES)
        if form.is_valid():
            appeal = form.save(commit=False)
            appeal.filing_voter = request.user
            appeal.election = election
            appeal.appeal_id = f"APPEAL-{uuid.uuid4().hex[:8].upper()}"
            appeal.status = ElectionAppeal.Status.SUBMITTED
            appeal.save()

            # Send notification
            send_appeal_received_notification(request.user, appeal)

            return redirect('appeal_confirmation', appeal_id=appeal.appeal_id)

    form = AppealForm()
    return render(request, 'appeal_form.html', {'form': form})
```

### Review Appeals (Admin)

**Admin UI Flow**

```
Admin → Election Appeals → [View Appeals]
- Filter by status
- View filing voter info
- Review description
- Add investigation notes
- Change status
```

**Approval Workflow**

```python
# views.py (admin)
def review_appeal(request, appeal_id):
    appeal = ElectionAppeal.objects.get(id=appeal_id)

    if request.method == 'POST':
        status = request.POST['status']  # APPROVED/REJECTED
        notes = request.POST['notes']

        appeal.status = status
        appeal.investigation_notes = notes
        appeal.reviewed_by = request.user
        appeal.resolved_at = timezone.now()
        appeal.save()

        # Notify voter of decision
        send_appeal_decision_notification(appeal)

        return redirect('appeals_list')

    return render(request, 'review_appeal.html', {'appeal': appeal})
```

### Appeal Types

```python
class ElectionAppeal(models.Model):
    class AppealType(models.TextChoices):
        VOTER_ELIGIBILITY = "VOTER_ELIGIBILITY"  # Dispute eligibility
        VOTE_VERIFICATION = "VOTE_VERIFICATION"  # Dispute verification
        RESULTS = "RESULTS"  # Challenge results
        CANDIDATE_DISPUTE = "CANDIDATE_DISPUTE"  # Candidate issue
        OTHER = "OTHER"  # Other grievance
```

---

## Party Performance

### Calculate Party Performance

**Automatic Calculation During Vote Tally**

```python
# After vote verification
from voting.models import PartyPerformance

def update_party_performance(election):
    parties = Party.objects.all()

    for party in parties:
        candidates = Candidate.objects.filter(
            party=party,
            constituency__election=election
        )

        total_votes = ResultTally.objects.filter(
            election=election,
            candidate__party=party
        ).aggregate(Sum('votes'))['votes__sum'] or 0

        total_candidates = candidates.count()
        elected = 0  # Count elected candidates

        total_registered = VoterProfile.objects.filter(
            constituency__election=election,
            is_verified=True
        ).count()

        vote_share = (total_votes / total_registered * 100) if total_registered > 0 else 0

        PartyPerformance.objects.update_or_create(
            party=party,
            election=election,
            defaults={
                'total_candidates': total_candidates,
                'elected_candidates': elected,
                'total_votes': total_votes,
                'vote_share_percentage': vote_share,
                'rank': 0  # Calculate ranking after all updated
            }
        )
```

### Display Party Performance

```python
# views.py
def party_performance(request, election_id):
    performance = PartyPerformance.objects.filter(
        election_id=election_id
    ).order_by('-vote_share_percentage')

    context = {
        'performance': performance
    }
    return render(request, 'party_performance.html', context)
```

**Template**

```html
<table class="performance-table">
  <thead>
    <tr>
      <th>Rank</th>
      <th>Party</th>
      <th>Candidates</th>
      <th>Elected</th>
      <th>Votes</th>
      <th>Vote Share</th>
    </tr>
  </thead>
  <tbody>
    {% for perf in performance %}
    <tr>
      <td>{{ forloop.counter }}</td>
      <td>{{ perf.party.name_en }}</td>
      <td>{{ perf.total_candidates }}</td>
      <td>{{ perf.elected_candidates }}</td>
      <td>{{ perf.total_votes }}</td>
      <td>{{ perf.vote_share_percentage|floatformat:1 }}%</td>
    </tr>
    {% endfor %}
  </tbody>
</table>
```

---

## Voting Statistics

### Update Voting Statistics

**Real-Time Updates (During Election)**

```python
# signal after each vote cast
from django.db.models.signals import post_save

@receiver(post_save, sender=EncryptedBallot)
def update_voting_stats(sender, instance, created, **kwargs):
    if created:
        stats = VotingStatistics.objects.get(
            election=instance.election
        )

        # Increment vote count
        stats.total_votes_cast += 1

        # Update by time
        now = timezone.now()
        hour = now.hour

        # Update hourly data
        if not stats.votes_by_time:
            stats.votes_by_time = []

        # Find or create hour entry
        hour_data = next(
            (h for h in stats.votes_by_time if h['hour'] == hour),
            None
        )

        if hour_data:
            hour_data['votes'] += 1
        else:
            stats.votes_by_time.append({'hour': hour, 'votes': 1})

        # Update peak hour
        stats.peak_voting_hour = max(
            stats.votes_by_time,
            key=lambda x: x['votes']
        )['hour']

        stats.save()
```

### Display Statistics Dashboard

```python
# views.py
def election_stats(request, election_id):
    stats = VotingStatistics.objects.get(election_id=election_id)

    context = {
        'total_votes': stats.total_votes_cast,
        'participation': stats.participation_rate,
        'peak_hour': stats.peak_voting_hour,
        'votes_by_gender': stats.votes_by_gender,
        'votes_by_age': stats.votes_by_age_group,
        'votes_by_time': stats.votes_by_time,
    }
    return render(request, 'statistics.html', context)
```

**Live Dashboard Example**

```html
<div class="stats-dashboard">
  <div class="stat-card">
    <h3>Total Votes</h3>
    <p class="big-number">{{ total_votes }}</p>
  </div>

  <div class="stat-card">
    <h3>Participation Rate</h3>
    <p class="big-number">{{ participation|floatformat:1 }}%</p>
  </div>

  <div class="stat-card">
    <h3>Peak Voting Hour</h3>
    <p class="big-number">{{ peak_hour }}:00</p>
  </div>

  <div class="chart">
    <!-- Chart showing votes by time -->
    <canvas id="votesChart"></canvas>
  </div>
</div>
```

---

## Debate Forum

### Configuration

**Step 1: Debate Post Moderation**

```
Admin → Debate Posts
- Check "Is Approved" to show public
- Check "Is Pinned" to feature
- View and manage categories
```

**Step 2: Comment Moderation**

```
Admin → Debate Comments
- Approve/reject comments
- Like/dislike counts
- Delete inappropriate content
```

### Create Discussion Posts

```python
# views.py
def create_debate_post(request, election_id):
    if request.method == 'POST':
        post = DebatePost.objects.create(
            topic=request.POST['topic'],
            description=request.POST['description'],
            election_id=election_id,
            created_by=request.user,
            category=request.POST.get('category', 'general'),
            is_approved=False  # Requires moderation
        )

        return redirect('debate_post_detail', post_id=post.id)

    return render(request, 'create_debate_post.html')
```

### Reply to Posts

```python
# views.py
def reply_to_post(request, post_id):
    post = DebatePost.objects.get(id=post_id)

    if request.method == 'POST':
        comment = DebateComment.objects.create(
            post=post,
            author=request.user,
            content=request.POST['content'],
            is_approved=False  # Requires moderation
        )

        # Update reply count
        post.total_replies += 1
        post.save()

        return redirect('debate_post_detail', post_id=post_id)

    return render(request, 'post_comment.html', {'post': post})
```

### Display Forum

```html
<!-- debate_forum.html -->
<div class="debate-forum">
  <h2>Election Discussion Forum</h2>

  <div class="posts-list">
    {% for post in posts %} {% if post.is_approved %}
    <div class="post-card {% if post.is_pinned %}pinned{% endif %}">
      {% if post.is_pinned %}
      <span class="pin-badge">📌 Featured</span>
      {% endif %}

      <h3>{{ post.topic }}</h3>
      <p class="metadata">
        Posted by {{ post.created_by.username }} on {{ post.created_at|date:"M
        d, Y" }}
      </p>
      <p>{{ post.description }}</p>

      <div class="post-stats">
        <span>💬 {{ post.total_replies }} replies</span>
        <span>👁 {{ post.total_views }} views</span>
      </div>

      <a href="{% url 'debate_post_detail' post.id %}" class="btn">
        View Discussion
      </a>
    </div>
    {% endif %} {% endfor %}
  </div>
</div>
```

---

## Compliance Reports

### Generate Compliance Report

**Step 1: Create Report in Admin**

```
Admin → Compliance Reports → Add Report
```

**Step 2: Fill Report Details**

```
Type: COMPLIANCE (or AUDIT, TRANSPARENCY, SECURITY)
Election: [Select election]
Title: "Election Integrity Compliance Report"
Content: [Detailed report content]
Generated By: [Your admin user]
PDF File: [Upload PDF if available]
Is Published: [Check to make public]
```

### Report Types

```python
class ComplianceReport(models.Model):
    class ReportType(models.TextChoices):
        AUDIT = "AUDIT"          # Process audit
        COMPLIANCE = "COMPLIANCE"  # Regulatory compliance
        TRANSPARENCY = "TRANSPARENCY"  # Public disclosure
        SECURITY = "SECURITY"    # Security assessment
```

### Generate PDF Report

```python
# utils.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_compliance_pdf(report):
    """Generate PDF version of compliance report"""
    filename = f"reports/{report.id}_{report.title}.pdf"

    c = canvas.Canvas(filename, pagesize=letter)

    # Add title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, report.title)

    # Add date
    c.setFont("Helvetica", 10)
    c.drawString(50, 730, f"Generated: {report.generated_at.strftime('%Y-%m-%d')}")

    # Add content
    c.setFont("Helvetica", 11)
    y = 700
    for line in report.content.split('\n'):
        c.drawString(50, y, line[:70])
        y -= 20
        if y < 50:
            c.showPage()
            y = 750

    c.save()
    report.pdf_file = filename
    report.save()
```

### Display Compliance Report

```python
# views.py
def view_compliance_report(request, report_id):
    report = ComplianceReport.objects.get(id=report_id)

    if not report.is_published and request.user not in Admin:
        return HttpResponseForbidden("Report not public")

    return render(request, 'compliance_report.html', {
        'report': report
    })
```

**Template**

```html
<!-- compliance_report.html -->
<div class="report-viewer">
  <div class="report-header">
    <h1>{{ report.title }}</h1>
    <p class="type-badge">{{ report.get_rtype_display }}</p>
    <p class="meta">
      Generated: {{ report.generated_at|date:"F d, Y" }} by {{
      report.generated_by.username }}
    </p>
  </div>

  <div class="report-content">{{ report.content|safe }}</div>

  {% if report.pdf_file %}
  <a href="{{ report.pdf_file.url }}" class="btn btn-primary">
    📄 Download PDF
  </a>
  {% endif %}
</div>
```

---

## Summary

All advanced features are designed to:

✅ **Enhance Transparency** - Compliance reports, audit logs
✅ **Increase Engagement** - Endorsements, surveys, forum
✅ **Provide Education** - Learning materials, tutorials
✅ **Track Performance** - Analytics, statistics
✅ **Enable Dispute Resolution** - Appeals system
✅ **Support Analysis** - Party performance, voting trends

Choose the features relevant to your election and enable them gradually for best results.
