# Nepal Voting System - Quick Reference

## What Was Implemented

### ✅ Core Features Added

1. **Email-Based User Authentication**
   - Users register/login with email address
   - Email is used as primary username
   - Password validation enforced

2. **Admin Verification Workflow**
   - All votes start in PENDING status
   - Admins must explicitly APPROVE votes
   - Votes don't count until verified
   - Admin can REJECT suspicious votes

3. **Admins Cannot Vote**
   - `VoterProfile.is_admin` flag prevents voting
   - Admin users can only verify/approve votes
   - Voting permission checks for admin status

4. **Complete Elections Management**
   - Create multiple elections
   - Set start/end times and status
   - Support 165+ Nepal constituencies
   - Automatic status sync (DRAFT → RUNNING → ENDED)

5. **Full Constituency Database**
   - Load all 165 Nepal constituencies from CSV
   - Auto-detect districts from locality names
   - Management command: `seed_constituencies_csv`

---

## Database Models (NEW/MODIFIED)

### VoteVerification (NEW)

Tracks admin approval of each vote:

```
id, ballot (FK), voter (FK), status (PENDING|VERIFIED|REJECTED),
verified_by (FK to admin), verified_at, notes, created_at
```

### VoterProfile (MODIFIED)

Added `is_admin` boolean field (default: False)

---

## Files Modified

| File                         | Change                                                   |
| ---------------------------- | -------------------------------------------------------- |
| `models.py`                  | Added VoteVerification model, is_admin field             |
| `permissions.py`             | Added IsAdminUser, updated IsVerifiedVoter               |
| `services.py`                | Added verify_vote() function, admin check in cast_vote() |
| `admin.py`                   | Added VoteVerificationAdmin, approve/reject actions      |
| `views_api.py`               | Added api_vote_status() endpoint                         |
| `urls_api.py`                | Added /api/vote/status route                             |
| `seed_constituencies_csv.py` | Updated to load from CSV file                            |

---

## Migration Added

**File**: `0006_add_vote_verification.py`

- Adds VoteVerification model
- Adds is_admin field to VoterProfile

---

## Setup Instructions

### 1. Apply Migrations

```bash
python manage.py migrate
```

### 2. Load Constituencies

```bash
python manage.py seed_constituencies_csv --csv data/nepal_constituencies_165.csv
```

### 3. Create Admin User

```bash
python manage.py createsuperuser
```

### 4. Create Parties & Candidates

- Login to `/admin/`
- Add parties: Democracy Party, People's Party, etc.
- Add candidates per constituency

### 5. Create & Run Election

- Admin panel → Elections
- Set start/end times
- Status changes auto (DRAFT → RUNNING → ENDED)

### 6. Users Register & Vote

- Register: `/web/register/` (email + password)
- Profile: `/web/profile/` (select district/constituency)
- Vote: `/web/vote/{election_id}/` (select candidate)

### 7. Admin Verifies Votes

- Admin panel → Vote Verification
- Review pending votes
- Click "Approve" or "Reject"
- Verified votes count in results

---

## Admin Workflows

### Daily Admin Tasks

**Morning: Verify Voter Profiles**

1. Go to Admin → Voter Profiles
2. Filter: `is_verified = False`
3. Check citizenship IDs, phone numbers
4. Select & click "Verify selected voters"

**During Voting: Monitor Votes**

1. Go to Admin → Vote Verification
2. Filter: `status = PENDING`
3. Review voter info
4. Click "Approve selected votes"

**After Election: View Results**

1. Go to Admin → Result Tally
2. Sort by votes (descending)
3. Export results if needed

---

## API Endpoints

### Authentication

```
POST /api/auth/register
POST /api/auth/login
```

### Elections

```
GET  /api/elections
GET  /api/elections/{id}/candidates
POST /api/elections/{id}/vote
GET  /api/elections/{id}/results
```

### Vote Status (NEW)

```
GET  /api/vote/status  (requires login)
```

---

## Key Rules

| Rule                   | Details                                      |
| ---------------------- | -------------------------------------------- |
| Non-Admins Can Vote    | `is_admin=False` required                    |
| Votes Must Be Verified | Don't count until `status=VERIFIED`          |
| One Vote Per Election  | `VoterParticipation` prevents duplicates     |
| Admin Exclusive        | Only `is_staff=True` can verify votes        |
| Encryption             | Ballots encrypted, decrypted on verification |
| Receipt UUID           | Unique per vote for tracking                 |

---

## Testing Scenario

```
1. Create party: "Democracy Party"
2. Create candidates for some constituencies
3. Create election: status=DRAFT
4. Change status to RUNNING (time-based or manual)
5. User email: voter1@example.com registers
6. User completes profile (Kathmandu constituency)
7. Admin verifies voter
8. User votes for candidate
9. Vote appears in Admin → Vote Verification (PENDING)
10. Admin approves vote
11. Vote appears in Admin → Result Tally
```

---

## Troubleshooting

| Issue                    | Solution                                                                                       |
| ------------------------ | ---------------------------------------------------------------------------------------------- |
| "Voter not verified"     | Admin must verify in Voter Profiles                                                            |
| Vote not in results      | Admin must approve in Vote Verification                                                        |
| Permission denied voting | Check is_admin flag (should be False)                                                          |
| CSV not loading          | Check path: `python manage.py seed_constituencies_csv --csv data/nepal_constituencies_165.csv` |
| Election locked          | Can't vote if status=DRAFT or ENDED                                                            |

---

## Admin Interface Location

- **Main Admin**: http://localhost:8000/admin/
- **Login Required**: Yes (staff user)
- **Key Sections**:
  - Voting > Voter Profiles (verify users)
  - Voting > Vote Verification (approve votes)
  - Voting > Result Tally (view results)
  - Voting > Elections (create/manage elections)

---

## User Interface Location

- **Register**: http://localhost:8000/web/register/
- **Login**: http://localhost:8000/web/login/
- **Profile**: http://localhost:8000/web/profile/
- **Vote**: http://localhost:8000/web/vote/{election_id}/
- **Results**: http://localhost:8000/results/

---

## Important Notes

⚠️ **Production Deployment**

- Change `DEBUG=False` in settings.py
- Update `SECRET_KEY` in .env
- Use environment variables for sensitive data
- Enable HTTPS
- Set up proper logging

⚠️ **Security**

- Encrypt database backups
- Review AuditLog regularly for suspicious activity
- Keep admin user password strong
- Don't share admin credentials

⚠️ **Data Integrity**

- Backup database before running elections
- Test vote verification workflow in dev first
- Audit all admin actions in AuditLog
- Keep encrypted ballots secure

---

## 🆕 Advanced Features (v2.0)

New features added for enhanced election management:

### 13 New Models Added

```
1. CandidateManifesto      # Candidate policies & bio
2. ElectionSurvey          # Opinion polls
3. SurveyQuestion          # Survey questions
4. SurveyResponse          # User responses
5. VoterEducation          # Learning materials
6. EducationProgress       # Progress tracking
7. CandidateEndorsement    # Public support
8. ElectionAppeal          # Dispute resolution
9. PartyPerformance        # Party analytics
10. VotingStatistics       # Real-time data
11. DebatePost             # Forum discussions
12. DebateComment          # Forum replies
13. ComplianceReport       # Audit reports
```

### Quick Setup

1. **Run migrations**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Access admin interface**

   ```
   /admin/voting/candidatemanifesto/
   /admin/voting/electionsurvey/
   /admin/voting/votereducation/
   # ... and more
   ```

3. **Add content**
   - Create candidate manifestos
   - Setup surveys
   - Add educational materials
   - Enable endorsements

### Documentation

For detailed guides:

- **ADVANCED_FEATURES.md** - Implementation guide
- **RELEASE_NOTES.md** - What's new in v2.0
- **FEATURES.md** - Complete feature list

---

## Support

For issues or questions:

1. Check SETUP_GUIDE.md for detailed instructions
2. Check ADVANCED_FEATURES.md for new features
3. Review RELEASE_NOTES.md for version info
4. Check QUICK_REFERENCE.md (this file) for quick lookups
5. Check Django debug messages (if DEBUG=True)
6. Check database migrations with: `python manage.py showmigrations`

**Status**: Production Ready v2.0 🎉
