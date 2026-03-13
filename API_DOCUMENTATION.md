# Nepal Voting System - API Documentation

## Base URL

```
https://yourdomain.com/api/
```

## Authentication

### Token Authentication

All endpoints except auth endpoints require token in header:

```
Authorization: Token YOUR_JWT_TOKEN
```

### OAuth Endpoints

Google OAuth endpoints return JWT token for use in subsequent requests.

---

## Authentication Endpoints

### 1. Register User

```http
POST /auth/register/
Content-Type: application/json

{
    "email": "voter@example.com",
    "password": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe"
}

Response 201:
{
    "id": 1,
    "email": "voter@example.com",
    "message": "Registration successful. Please verify your email."
}
```

### 2. Send OTP

```http
POST /auth/send-otp/
Content-Type: application/json

{
    "email": "voter@example.com"
}

Response 200:
{
    "message": "OTP sent to your email. Valid for 10 minutes."
}
```

### 3. Verify OTP

```http
POST /auth/verify-otp/
Content-Type: application/json

{
    "email": "voter@example.com",
    "otp_code": "123456"
}

Response 200:
{
    "message": "Email verified successfully!",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 4. Login

```http
POST /auth/login/
Content-Type: application/json

{
    "email": "voter@example.com",
    "password": "SecurePassword123!"
}

Response 200:
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": 1,
        "email": "voter@example.com",
        "first_name": "John"
    }
}
```

### 5. Google OAuth Login

```http
POST /auth/google-oauth/
Content-Type: application/json

{
    "token": "google_oauth_token"
}

Response 200:
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {...},
    "created": true
}
```

### 6. Password Reset Request

```http
POST /auth/password-reset/
Content-Type: application/json

{
    "email": "voter@example.com"
}

Response 200:
{
    "message": "Password reset link sent to your email."
}
```

### 7. Reset Password Confirm

```http
POST /auth/password-reset-confirm/
Content-Type: application/json

{
    "token": "reset-token",
    "new_password": "NewPassword123!"
}

Response 200:
{
    "message": "Password reset successfully."
}
```

### 8. Logout

```http
POST /auth/logout/
Authorization: Token YOUR_TOKEN

Response 200:
{
    "message": "Logged out successfully."
}
```

---

## User Profile Endpoints

### 1. Get Profile

```http
GET /profile/
Authorization: Token YOUR_TOKEN

Response 200:
{
    "id": 1,
    "user": {
        "id": 1,
        "email": "voter@example.com",
        "first_name": "John"
    },
    "unique_voter_id": "VP-20240312120000-ABC123",
    "date_of_birth": "1995-05-15",
    "age": 28,
    "profile_photo": "https://...",
    "citizenship_id": "12345678",
    "phone": "+977-9841234567",
    "district": 1,
    "constituency": 5,
    "is_verified": true,
    "email_verified": true,
    "is_admin": false,
    "is_eligible_to_vote": true,
    "created_at": "2024-03-12T10:30:00Z"
}
```

### 2. Update Profile

```http
PUT /profile/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
    "date_of_birth": "1995-05-15",
    "citizenship_id": "12345678",
    "phone": "+977-9841234567",
    "district": 1,
    "constituency": 5
}

Response 200:
{
    "message": "Profile updated successfully",
    "profile": {...}
}
```

### 3. Upload Profile Photo

```http
POST /profile/upload-photo/
Authorization: Token YOUR_TOKEN
Content-Type: multipart/form-data

{
    "photo": <image file>
}

Response 200:
{
    "message": "Photo uploaded successfully",
    "photo_url": "https://..."
}
```

### 4. Check Voter Eligibility

```http
GET /profile/eligibility/
Authorization: Token YOUR_TOKEN

Response 200:
{
    "is_eligible": true,
    "reasons": [],
    "missing_requirements": []
}

Response 400:
{
    "is_eligible": false,
    "reasons": [
        "Email not verified",
        "Profile not approved by admin",
        "Age under 18"
    ]
}
```

---

## Elections Endpoints

### 1. List Elections

```http
GET /elections/?status=RUNNING&limit=10&offset=0
Authorization: Token YOUR_TOKEN (optional)

Response 200:
{
    "count": 5,
    "next": "https://...",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Nepal Parliamentary Election 2024",
            "description": "...",
            "start_at": "2024-04-01T08:00:00Z",
            "end_at": "2024-04-01T17:00:00Z",
            "status": "RUNNING",
            "is_running": true,
            "has_ended": false,
            "constituencies_count": 165
        }
    ]
}
```

### 2. Get Election Detail

```http
GET /elections/{id}/
Authorization: Token YOUR_TOKEN

Response 200:
{
    "id": 1,
    "title": "Nepal Parliamentary Election 2024",
    "description": "...",
    "start_at": "2024-04-01T08:00:00Z",
    "end_at": "2024-04-01T17:00:00Z",
    "status": "RUNNING",
    "constituencies": [
        {
            "id": 1,
            "code": "KAM-1",
            "name": "Kathmandu-1",
            "district": "Kathmandu"
        }
    ],
    "statistics": {
        "total_registered_voters": 1500000,
        "total_votes_cast": 750000,
        "voter_participation_rate": 50.0
    }
}
```

### 3. Get Election Statistics

```http
GET /elections/{id}/statistics/
Authorization: Token YOUR_TOKEN

Response 200:
{
    "election_id": 1,
    "total_registered_voters": 1500000,
    "total_votes_cast": 750000,
    "total_votes_verified": 749000,
    "voter_participation_rate": 50.0,
    "by_constituency": {...},
    "by_district": {...},
    "updated_at": "2024-03-12T15:30:00Z"
}
```

### 4. Get Constituencies

```http
GET /elections/{id}/constituencies/
Authorization: Token YOUR_TOKEN

Response 200:
[
    {
        "id": 1,
        "code": "KAM-1",
        "name": "Kathmandu-1",
        "district": "Kathmandu"
    }
]
```

---

## Candidate Endpoints

### 1. List Candidates

```http
GET /elections/{id}/candidates/?constituency=5&search=Kumar
Authorization: Token YOUR_TOKEN

Response 200:
[
    {
        "id": 1,
        "full_name_en": "Ram Kumar Sharma",
        "full_name_np": "राम कुमार शर्मा",
        "party": {
            "id": 1,
            "name_en": "Democracy Party",
            "abbreviation": "DP",
            "symbol": "🐘"
        },
        "photo": "https://...",
        "constituency": "Kathmandu-1"
    }
]
```

### 2. Get Candidate Detail

```http
GET /elections/{id}/candidates/{candidate_id}/
Authorization: Token YOUR_TOKEN

Response 200:
{
    "id": 1,
    "full_name_en": "Ram Kumar Sharma",
    "full_name_np": "राम कुमार शर्मा",
    "party": {...},
    "photo": "https://...",
    "constituency": "Kathmandu-1",
    "metadata": {
        "biography": "...",
        "achievements": "...",
        "policies": "...",
        "contact_email": "candidate@example.com",
        "website": "https://...",
        "social_media": {
            "twitter": "@username",
            "facebook": "..."
        }
    }
}
```

### 3. Create Candidate (Admin Only)

```http
POST /candidates/
Authorization: Token ADMIN_TOKEN
Content-Type: application/json

{
    "full_name_en": "Ram Kumar Sharma",
    "full_name_np": "राम कुमार शर्मा",
    "party_id": 1,
    "constituency_id": 5,
    "photo": "image_file"
}

Response 201:
{
    "id": 1,
    ...
}
```

---

## Voting Endpoints

### 1. Cast Vote

```http
POST /elections/{id}/vote/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
    "candidate_id": 1
}

Response 201:
{
    "receipt_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "status": "PENDING",
    "message": "Vote cast successfully. Awaiting admin verification."
}

Possible Errors:
400: "Election is not currently accepting votes"
400: "You are not verified yet"
400: "You have already voted in this election"
403: "Admin users cannot vote"
```

### 2. Check Vote Status

```http
GET /vote/status/
Authorization: Token YOUR_TOKEN

Response 200:
{
    "user_email": "voter@example.com",
    "votes": [
        {
            "election_id": 1,
            "election_title": "Nepal Parliamentary Election 2024",
            "status": "VERIFIED",
            "receipt_uuid": "550e8400-e29b-41d4-a716-446655440000",
            "voted_at": "2024-03-12T10:30:00Z",
            "verified_at": "2024-03-12T11:00:00Z"
        }
    ]
}
```

### 3. Get Vote Receipt

```http
GET /elections/{id}/vote-receipt/{receipt_uuid}/
Authorization: Token YOUR_TOKEN

Response 200:
{
    "receipt_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "election": "Nepal Parliamentary Election 2024",
    "constituency": "Kathmandu-1",
    "voted_at": "2024-03-12T10:30:00Z",
    "status": "VERIFIED",
    "verification_status": "Approved by admin"
}
```

---

## Results Endpoints

### 1. Get Results

```http
GET /elections/{id}/results/?constituency=5
Authorization: Token YOUR_TOKEN

Response 200:
{
    "election_id": 1,
    "election_title": "Nepal Parliamentary Election 2024",
    "completed": true,
    "results": [
        {
            "rank": 1,
            "candidate_name": "Ram Kumar Sharma",
            "party": "Democracy Party",
            "votes": 15000,
            "percentage": 35.7,
            "photo": "https://..."
        }
    ]
}

Note: Only available after election ends
```

### 2. Get Results Charts

```http
GET /elections/{id}/results/charts/
Authorization: Token YOUR_TOKEN

Response 200:
{
    "type": "bar|pie|line",
    "labels": ["Candidate A", "Candidate B"],
    "data": [15000, 12000],
    "total_votes": 27000
}
```

### 3. Get Results by Constituency

```http
GET /elections/{id}/results/by-constituency/
Authorization: Token YOUR_TOKEN

Response 200:
{
    "KAM-1": {
        "total_votes": 5000,
        "results": [...]
    },
    "KAM-2": {
        "total_votes": 4500,
        "results": [...]
    }
}
```

---

## Notification Endpoints

### 1. Get Notifications

```http
GET /notifications/?read=false&limit=10&offset=0
Authorization: Token YOUR_TOKEN

Response 200:
[
    {
        "id": 1,
        "type": "ELECTION_START",
        "title": "Election Starting",
        "message": "Nepal Parliamentary Election 2024 starts soon...",
        "read": false,
        "created_at": "2024-03-12T10:00:00Z"
    }
]
```

### 2. Mark Notification as Read

```http
PUT /notifications/{id}/read/
Authorization: Token YOUR_TOKEN

Response 200:
{
    "message": "Notification marked as read",
    "notification": {...}
}
```

### 3. Delete Notification

```http
DELETE /notifications/{id}/
Authorization: Token YOUR_TOKEN

Response 204
```

---

## Dashboard Endpoints

### 1. Admin Dashboard Data

```http
GET /dashboard/admin/
Authorization: Token ADMIN_TOKEN

Response 200:
{
    "total_voters": 1500000,
    "verified_voters": 1200000,
    "total_votes_cast": 750000,
    "pending_verifications": 5000,
    "active_elections": 1,
    "candidates": 825,
    "suspicious_activities": [...]
}
```

### 2. User Dashboard Data

```http
GET /dashboard/user/
Authorization: Token YOUR_TOKEN

Response 200:
{
    "profile_complete": true,
    "verification_status": "approved",
    "eligibility": "eligible",
    "current_election": {
        "id": 1,
        "title": "Nepal Parliamentary Election 2024",
        "status": "RUNNING",
        "time_remaining": "3 hours 30 minutes"
    },
    "vote_status": {
        "has_voted": true,
        "verification_status": "verified"
    },
    "past_elections": [...]
}
```

---

## Error Responses

### 400 Bad Request

```json
{
  "error": "Bad Request",
  "message": "Invalid input data",
  "details": {
    "field_name": ["Error message"]
  }
}
```

### 401 Unauthorized

```json
{
  "error": "Unauthorized",
  "message": "Authentication credentials were not provided."
}
```

### 403 Forbidden

```json
{
  "error": "Forbidden",
  "message": "You do not have permission to access this resource."
}
```

### 404 Not Found

```json
{
  "error": "Not Found",
  "message": "Resource not found."
}
```

### 429 Too Many Requests

```json
{
  "error": "Rate Limited",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

---

## Rate Limiting

- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour
- Login endpoint: 5 attempts/15 minutes

---

## Pagination

All list endpoints support:

- `limit`: Number of results (default: 20, max: 100)
- `offset`: Pagination offset (default: 0)

---

## Filtering & Search

Available query parameters:

- `search`: Search by name/email
- `status`: Filter by status
- `election_id`: Filter by election
- `constituency_id`: Filter by constituency
- `read`: Filter notifications (true/false)

---

## Sorting

Default sorting: `-created_at` (newest first)

Sortable fields:

- `created_at`
- `votes`
- `name`
- `date_of_birth`

Usage:

```
GET /candidates/?ordering=-votes
GET /notifications/?ordering=created_at
```
