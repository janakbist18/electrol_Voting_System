# Nepal Voting System - Setup Guide

## New Features Implemented

### 1. **Email-Based Authentication** ✅

- Users register and login with their email
- Passwords are securely hashed
- Email is used as unique username

### 2. **Admin Verification Workflow** ✅

- All votes start in **PENDING** status
- Admins must review and **APPROVE** or **REJECT** votes before they count
- Vote verification is tracked in the **VoteVerification** model
- Only verified votes count toward results

### 3. **Admins Cannot Vote** ✅

- Admin users cannot register as voters
- If `VoterProfile.is_admin = True`, voting is blocked
- Admin users can only verify other voters' votes

### 4. **Complete Elections Management** ✅

- Multiple elections can run simultaneously
- Elections have:
  - Title & Description
  - Start & End times
  - Status: DRAFT → RUNNING → ENDED
  - Automatic status sync based on time
- Constituencies are loaded from CSV file
- All 165 Nepal constituencies can be imported

### 5. **Vote Verification System** ✅

- New `VoteVerification` model tracks each vote's approval status
- Admin interface has bulk approve/reject actions
- Encrypted ballots are secure until verified
- ResultTally updates only when vote is verified

---

## Setup Instructions

### Step 1: Apply Migrations

```bash
cd nepal_voting
python manage.py makemigrations
python manage.py migrate
```

### Step 2: Load Constituencies from CSV

```bash
python manage.py seed_constituencies_csv --csv data/nepal_constituencies_165.csv --election "Nepal Parliamentary Election 2024"
```

This will:

- Create 165 constituencies
- Automatically detect districts from constituency names
- Create an election in DRAFT status ready to be configured

### Step 3: Create Admin User

```bash
python manage.py createsuperuser
# Follow prompts to create admin account
```

### Step 4: Create Parties and Candidates (Optional)

You can add parties and candidates through the admin panel at `/admin/`:

1. Go to `http://localhost:8000/admin/`
2. Login with your admin credentials
3. Add Parties (e.g., "Elephant Party", "Tiger Party")
4. Add Candidates (link to party, constituency, upload photo)

### Step 5: Configure and Run an Election

1. Go to Admin → Elections
2. Create or edit an election
3. Set Start and End times
4. Change status from DRAFT to RUNNING
5. Constituencies are auto-linked (already created from CSV)

### Step 6: User Registration & Voting

Users can now:

1. Register with email and password at `/web/register/`
2. Complete profile with district, constituency, citizenship ID
3. Admin verifies their profile at `/admin/voting/voterprofile/`
4. User votes at `/web/vote/{election_id}/`
5. Vote appears in pending verification
6. Admin verifies or rejects the vote at `/admin/voting/voteverification/`

---

## Key Models

### VoteVerification (NEW!)

```python
class VoteVerification(models.Model):
    ballot                  # OneToOne relation to EncryptedBallot
    voter                   # ForeignKey to User
    status                  # PENDING | VERIFIED | REJECTED
    verified_by             # ForeignKey to Admin User
    verified_at             # DateTime
    notes                   # Text field for admin notes
    created_at              # Auto timestamp
```

### VoterProfile (UPDATED)

```python
class VoterProfile(models.Model):
    user                    # OneToOne
    is_verified             # Default: False (admin must verify)
    is_admin                # NEW! Default: False (set for admin users)
    district, constituency  # Election location
    citizenship_id, phone   # Identity info
```

### Election (EXISTS)

```python
class Election(models.Model):
    title, description
    start_at, end_at        # DateTime
    status                  # DRAFT | RUNNING | ENDED (auto-sync)
    created_at
```

---

## Admin Workflow

### For Admin Users:

1. **Verify Voters**: Admin → Voter Profiles → Select users → "Verify selected voters"
2. **Approve Votes**: Admin → Vote Verification → Select pending votes → "Approve selected votes"
3. **Reject Votes**: Admin → Vote Verification → Select votes → "Reject selected votes"
4. **View Results**: Admin → Result Tally (shows verified vote counts only)
5. **Audit Log**: View all system actions in Admin → Audit Logs

### Admin Actions Available:

- ✅ Verify voters (set `is_verified=True`)
- ✅ Approve votes (move from PENDING → VERIFIED, update tallies)
- ❌ Reject votes (move to REJECTED, don't count them)
- View voter profiles
- View pending/verified/rejected votes
- Mark users as admin (`is_admin=True` prevents them from voting)

---

## Voting Flow

```
1. User registers with email
   ↓
2. User completes profile (constituency)
   ↓
3. Admin verifies user profile
   ↓
4. User clicks "Vote" and selects candidate
   ↓
5. Vote is cast (CREATES encrypted ballot + pending verification)
   ↓
6. Admin reviews vote in "Vote Verification" admin panel
   ↓
7. Admin clicks "Approve" or "Reject"
   ↓
   IF APPROVED: Vote counts toward ResultTally
   IF REJECTED: Vote is ignored
   ↓
8. Election ends (status → ENDED)
   ↓
9. Results are available for public viewing (ResultTally)
```

---

## API Endpoints (Optional)

If using REST API instead of web interface:

```
POST   /api/auth/register          - Register new voter
POST   /api/auth/login             - Login with email
GET    /api/elections/             - List all elections
GET    /api/elections/{id}/candidates/?constituency=X - Get candidates
POST   /api/elections/{id}/vote/   - Cast vote (verified voters only)
GET    /api/elections/{id}/results/ - View results (after election ends)
```

---

## Important Notes

⚠️ **Admin Users Cannot Vote**

- If `VoterProfile.is_admin = True`, voting permission is denied
- Use this flag to prevent staff from voting

📝 **All Votes Are Pending by Default**

- Votes don't count toward results until admin verifies them
- Find pending votes in Admin → Vote Verification (status = "Pending")

🔒 **Encrypted Ballots**

- Ballots are encrypted until verified
- Admin can see voter email but not vote choice before decryption
- Each vote has a unique receipt_uuid for tracking

📊 **Results Only After Election Ends**

- Results are hidden until election status = ENDED
- Auto-calculated from verified votes only
- `ResultTally` updates when admin approves votes

---

## Testing the System

```bash
# Start development server
python manage.py runserver

# Register a test voter
# - Go to http://localhost:8000/web/register/
# - Email: voter1@example.com, Password: TestPass123

# Complete profile
# - Go to http://localhost:8000/web/profile/
# - Select district and constituency

# As admin, verify voter
# - Go to http://localhost:8000/admin/
# - Voting → Voter Profiles → Select voter → Verify

# Voter casts vote
# - Go to http://localhost:8000/web/vote/1/
# - Select candidate, vote cast (PENDING status)

# Admin approves vote
# - Admin → Vote Verification → Select vote → "Approve selected votes"
# - Vote is now VERIFIED and counts in results
```

---

## Files Modified

1. `voting/models.py` - Added VoteVerification, is_admin to VoterProfile
2. `voting/permissions.py` - Updated IsVerifiedVoter to check is_admin
3. `voting/services.py` - Updated cast_vote(), added verify_vote()
4. `voting/admin.py` - Added VoteVerificationAdmin, vote verification actions
5. `voting/management/commands/seed_constituencies_csv.py` - Updated to load from CSV

---

## Troubleshooting

### Q: "Voter is not verified" error when voting

**A:** Admin needs to go to Admin → Voter Profiles and click "Verify selected voters"

### Q: Vote doesn't count in results

**A:** Admin needs to approve it in Admin → Vote Verification → "Approve selected votes"

### Q: Admin user trying to vote gets permission denied

**A:** This is expected. Set `is_admin=False` in VoterProfile if they should vote.

### Q: Constituencies not loading from CSV

**A:** Run: `python manage.py seed_constituencies_csv --csv data/nepal_constituencies_165.csv`

### Q: Election status not updating automatically

**A:** Run `election.sync_status()` or reload page. Status auto-syncs on every request.

---

## Production Checklist

- [ ] Set `DEBUG = False` in settings.py
- [ ] Update `SECRET_KEY` in .env
- [ ] Set `ALLOWED_HOSTS` correctly
- [ ] Use strong admin password
- [ ] Enable HTTPS (set `SECURE_SSL_REDIRECT = True`)
- [ ] Configure database backup
- [ ] Set up logging to track admin actions
- [ ] Test vote verification workflow
- [ ] Review AuditLog for suspicious activity
