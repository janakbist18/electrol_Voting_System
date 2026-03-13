# Nepal Voting System - Complete Architecture

## Project Structure

```
nepal_voting/
├── nepal_voting/                    # Main project settings
│   ├── settings.py
│   ├── urls.py
│   └── security_middleware.py       # NEW: Rate limiting, CSRF
│
├── voting/                          # Main voting app
│   ├── models.py                    # Enhanced models
│   ├── forms.py                     # Registration, candidate, voting forms
│   ├── views.py                     # Page views
│   ├── views_api.py                 # REST API endpoints
│   ├── views_dashboard.py           # NEW: Admin & User dashboards
│   ├── admin.py                     # Django admin interface
│   ├── serializers.py               # DRF serializers
│   ├── permissions.py               # Custom permissions
│   ├── services.py                  # Business logic
│   ├── signals.py                   # Post-save signals
│   ├── notifications.py             # NEW: Email/SMS notifications
│   ├── utils.py                     # NEW: Utility functions
│   │
│   ├── management/
│   │   └── commands/
│   │       ├── seed_constituencies_csv.py
│   │       ├── seed_demo_data.py        # NEW: Demo parties, candidates
│   │       └── send_notifications.py    # NEW: Scheduled notifications
│   │
│   ├── migrations/
│   │   └── 0007_enhanced_features.py    # NEW: Enhanced models
│   │
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   └── templates/
│       ├── base.html
│       ├── home.html
│       ├── auth/
│       │   ├── login.html
│       │   ├── register.html
│       │   ├── verify_otp.html         # NEW
│       │   ├── google_oauth.html        # NEW
│       │   └── reset_password.html      # NEW
│       ├── dashboard/
│       │   ├── admin_dashboard.html     # NEW
│       │   ├── user_dashboard.html      # NEW
│       │   └── results.html
│       ├── candidate/
│       │   ├── candidate_list.html      # NEW
│       │   ├── candidate_detail.html    # NEW
│       │   └── manage_candidates.html   # NEW (admin)
│       ├── voter/
│       │   ├── profile.html
│       │   ├── vote.html
│       │   └── receipt.html
│       └── results/
│           └── results.html
│
├── requirements.txt                 # Updated dependencies
├── .env.example                     # Environment variables
├── ARCHITECTURE.md                  # This file
├── FEATURES.md                      # Feature list
└── API_DOCUMENTATION.md             # API reference

```

## Database Schema

### Core Models

```
User (Django)
├── voter_profile (1-1 with VoterProfile)
├── participations (M-1 with VoterParticipation)
└── votes (M-1 with VoteVerification)

VoterProfile
├── user (1-1)
├── unique_voter_id (unique)
├── date_of_birth (for age verification)
├── profile_photo
├── citizenship_id
├── phone
├── district (FK)
├── constituency (FK)
├── is_verified (by admin)
├── is_admin
├── otp_code (temporary)
├── otp_expires_at
├── email_verified (boolean)
├── google_oauth_id
└── metadata (JSON: IP, last_login, etc.)

Election
├── title
├── description
├── start_at
├── end_at
├── status
├── created_at
└── constituencies (M-1)

District
└── name_en, name_np

Constituency
├── election (FK)
├── district (FK)
├── code
├── name
└── candidates (M-1)

Party
├── name_en
├── name_np
├── abbreviation
└── symbol_text

Candidate
├── full_name_en
├── full_name_np
├── party (FK)
├── constituency (FK)
├── photo
├── description
└── tallies (M-1)

VoterParticipation
├── voter (FK)
├── election (FK)
├── has_voted
└── voted_at

EncryptedBallot
├── election (FK)
├── constituency (FK)
├── receipt_uuid
├── encrypted_payload
└── verification (1-1)

VoteVerification
├── ballot (1-1)
├── voter (FK)
├── status (PENDING/VERIFIED/REJECTED)
├── verified_by (FK to admin)
├── verified_at
├── notes
└── created_at

ResultTally
├── election (FK)
├── constituency (FK)
├── candidate (FK)
├── votes
└── percentage

AuditLog
├── actor (FK - admin)
├── action
├── object_type
├── object_id
├── meta_json
├── ip
├── ua
├── created_at
└── hash

Notification (NEW)
├── user (FK)
├── election (FK)
├── type (ELECTION_START, VOTING_REMINDER, RESULT_ANNOUNCEMENT)
├── title
├── message
├── sent_at
└── read_at

ElectionStatistics (NEW)
├── election (FK)
├── total_voters
├── total_votes
├── voter_participation_rate
├── updated_at
└── by_constituency (JSON)

CandidateMetadata (NEW)
├── candidate (1-1)
├── bio
├── achievements
├── policies
└── contact_info
```

## API Endpoints (Complete List)

### Authentication

```
POST   /api/auth/register/              - Register user
POST   /api/auth/verify-otp/            - Verify OTP
POST   /api/auth/login/                 - Login
POST   /api/auth/login-google/          - Google OAuth
POST   /api/auth/logout/                - Logout
POST   /api/auth/reset-password/        - Reset password
POST   /api/auth/confirm-reset/         - Confirm password reset
```

### User Profile

```
GET    /api/profile/                    - Get user profile
PUT    /api/profile/                    - Update profile
POST   /api/profile/upload-photo/       - Upload profile photo
GET    /api/profile/verify-age/         - Check age verification
```

### Elections

```
GET    /api/elections/                  - List all elections
GET    /api/elections/{id}/             - Get election details
GET    /api/elections/{id}/stats/       - Get election statistics
GET    /api/elections/{id}/constituencies/ - Get constituencies
GET    /api/elections/{id}/notification- Election status notification
```

### Candidates

```
GET    /api/elections/{id}/candidates/  - List candidates
GET    /api/elections/{id}/candidates/{cid}/ - Candidate details
POST   /api/candidates/                 - Create candidate (admin)
PUT    /api/candidates/{id}/            - Update candidate (admin)
DELETE /api/candidates/{id}/            - Delete candidate (admin)
```

### Voting

```
POST   /api/elections/{id}/vote/        - Cast vote
GET    /api/vote/status/                - Check vote status
POST   /api/vote/verify/                - Verify vote (admin)
```

### Results

```
GET    /api/elections/{id}/results/     - Get results (after election)
GET    /api/elections/{id}/results/charts/ - Chart data
GET    /api/elections/{id}/results/by-constituency/ - By constituency
```

### Dashboards

```
GET    /api/dashboard/admin/            - Admin dashboard data
GET    /api/dashboard/user/             - User dashboard data
GET    /api/dashboard/admin/voters/     - Voter management
GET    /api/dashboard/admin/votes/      - Vote verification
```

### Notifications

```
GET    /api/notifications/              - Get notifications
PUT    /api/notifications/{id}/read/    - Mark as read
DELETE /api/notifications/{id}/         - Delete notification
```

### Audit

```
GET    /api/audit-logs/                 - View audit logs (admin)
GET    /api/audit-logs/search/          - Search audit logs
```

## Security Features

### Authentication

- ✅ Email/Password registration
- ✅ OTP verification (via email)
- ✅ Google OAuth 2.0
- ✅ Password reset with token
- ✅ JWT/Token authentication
- ✅ Session management

### Authorization

- ✅ Role-based access control (admin/voter)
- ✅ Age verification (18+)
- ✅ Email verification required
- ✅ Unique voter ID (prevent duplicates)
- ✅ Admin approval required to vote

### API Security

- ✅ Rate limiting (DRF throttle)
- ✅ CSRF protection
- ✅ CORS configuration
- ✅ Token authentication
- ✅ Input validation & sanitization

### Vote Security

- ✅ Encrypted ballots (Fernet)
- ✅ IP logging (voter location)
- ✅ Session timeout
- ✅ Vote tampering detection (hash chain)
- ✅ Admin cannot see vote-to-voter mapping

### Data Protection

- ✅ HTTPS enforcement
- ✅ SQL injection prevention (ORM)
- ✅ XSS protection (template escaping)
- ✅ CSRF tokens on all forms
- ✅ Secure password hashing (bcrypt)

### Additional

- ✅ Captcha on login/register
- ✅ Suspicious activity detection
- ✅ Audit logging (immutable)
- ✅ Data retention policies

## Feature Implementation Status

| Feature               | Status | Priority |
| --------------------- | ------ | -------- |
| Email Registration    | ✅     | HIGH     |
| OTP Verification      | 🔄     | HIGH     |
| Google OAuth          | 🔄     | MEDIUM   |
| Password Reset        | 🔄     | MEDIUM   |
| Profile Photo         | 🔄     | MEDIUM   |
| Age Verification      | 🔄     | HIGH     |
| Unique Voter ID       | 🔄     | HIGH     |
| Candidate Management  | 🔄     | HIGH     |
| Vote Encryption       | ✅     | HIGH     |
| CSRF Protection       | ✅     | HIGH     |
| Token Auth            | 🔄     | MEDIUM   |
| IP Logging            | 🔄     | MEDIUM   |
| Result System         | 🔄     | HIGH     |
| Charts/Analytics      | 🔄     | MEDIUM   |
| Audit Logs            | ✅     | HIGH     |
| Notifications         | 🔄     | MEDIUM   |
| Dashboards            | 🔄     | HIGH     |
| Rate Limiting         | 🔄     | HIGH     |
| CAPTCHA               | 🔄     | MEDIUM   |
| Session Timeout       | 🔄     | MEDIUM   |
| Privacy (Admin blind) | 🔄     | HIGH     |

Legend: ✅ Done | 🔄 In Progress | ⭕ Not Started

## Technology Stack

- **Backend**: Django 4.2+ | DRF
- **Database**: PostgreSQL (recommended) / SQLite (dev)
- **Authentication**: JWT + OAuth 2.0
- **Encryption**: Fernet (cryptography)
- **OTP**: pyotp
- **Email**: Django-anymail
- **SMS**: Twilio
- **Rate Limiting**: DRF throttles
- **CAPTCHA**: django-recaptcha
- **Charts**: Chart.js / Plotly
- **Frontend**: HTML5, Bootstrap 5, JavaScript

## Environment Variables

```env
# Django
DEBUG=False
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:password@host:5432/voting

# Email
EMAIL_BACKEND=anymail.backends.sendgrid.EmailBackend
SENDGRID_API_KEY=your-key

# SMS
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+1234567890

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-secret

# Security
ALLOWED_HOSTS=localhost,yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True

# Encryption
FERNET_KEY=your-fernet-key

# CAPTCHA
RECAPTCHA_PUBLIC_KEY=your-public-key
RECAPTCHA_PRIVATE_KEY=your-private-key

# OTP
OTP_LENGTH=6
OTP_VALIDITY_MINUTES=10

# Notifications
NOTIFICATION_EMAIL_SENDER=noreply@yourdomain.com
```

## Deployment Checklist

- [ ] Set DEBUG=False
- [ ] Update SECRET_KEY
- [ ] Configure DATABASE_URL (PostgreSQL)
- [ ] Setup email service (SendGrid)
- [ ] Setup SMS service (Twilio)
- [ ] Configure Google OAuth
- [ ] Enable HTTPS/SSL
- [ ] Setup CAPTCHA
- [ ] Configure rate limiting
- [ ] Enable audit logging
- [ ] Setup monitoring
- [ ] Configure backups
- [ ] Test security features
- [ ] Load test system

## Development Commands

```bash
# Setup
python manage.py migrate
python manage.py seed_constituencies_csv
python manage.py seed_demo_data

# Running
python manage.py runserver
celery -A nepal_voting worker -l info  # For async tasks

# Testing
python manage.py test
pytest voting/tests/

# Admin
python manage.py createsuperuser
python manage.py changepassword username

# Database
python manage.py dumpdata > backup.json
python manage.py loaddata backup.json
```

## Next Steps

1. ✅ Enhanced models implementation
2. 🔄 Forms and serializers
3. 🔄 Authentication views and APIs
4. 🔄 Notification system
5. 🔄 Dashboard views
6. 🔄 Security features
7. 🔄 Testing and documentation
