# AI Support Ticketing Backend

A production-style backend API for an AI-powered support ticketing system.

The system allows users to submit support tickets, which are automatically analyzed by AI to classify issues, determine urgency, and generate draft responses for support agents.

---

## 🚀 Features

### Authentication System
- User registration with password strength validation
- Secure login with JWT access tokens
- Refresh token with rotation and revocation (stored in DB)
- Logout support
- Password hashing using Argon2
- Role-based access control (RBAC)

### Ticket Management
- Create, view, update, and close support tickets
- Priority levels: `low`, `medium`, `high`, `critical`
- Categories: `general`, `billing`, `technical`, `other`
- Status tracking: `open`, `in_progress`, `resolved`, `closed`
- Admins see all tickets; users see only their own

### AI Features
- **Auto-classification** on ticket creation (category + priority + summary)
- **Manual re-classification** endpoint with optional apply toggle
- **Draft response generation** for support agents (uses comment history as context)
- Full AI result history stored per ticket

### Ticket Comments
- Public comments visible to all parties
- Internal notes visible only to agents and admins
- Authors embedded in responses
- Edit and delete with proper ownership checks

### Database Layer
- PostgreSQL
- SQLAlchemy ORM
- Alembic migration management

### Security
- JWT access tokens (short-lived)
- Opaque refresh tokens (long-lived, stored in DB, rotated on use)
- Argon2 password hashing
- Environment-based configuration
- Docs hidden in production

### Architecture
- Clean service-based architecture
- Separation of concerns (models / schemas / services / routes)
- Scalable modular project structure

### Testing
- 63 automated tests with Pytest
- Separate test database with per-test transaction rollback
- OpenAI calls mocked for fast, cost-free test runs

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Language | Python 3.12+ |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Auth | JWT (python-jose) + Argon2 (passlib) |
| Validation | Pydantic v2 |
| AI | OpenAI API (gpt-4o-mini) |
| Testing | Pytest + httpx |

---

## 📁 Project Structure

```
app/
├── auth/           # Registration, login, refresh, logout, JWT
├── tickets/        # Ticket CRUD and status management
├── comments/       # Per-ticket comments and internal notes
├── ai/             # Classification, draft generation, result history
├── core/           # Config and settings
└── db/             # Database session and base

alembic/
└── versions/       # Migration files

tests/
├── conftest.py     # Fixtures, test DB, helpers
├── test_auth.py
├── test_tickets.py
├── test_comments.py
└── test_ai.py
```

---

## ⚙️ Environment Setup

Create a `.env` file in the project root:

```env
ENV=development

DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_support_db

SECRET_KEY=your_secret_key_here
ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

PASSWORD_HASH_SCHEME=argon2

OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=30
```

> `OPENAI_API_KEY` is optional — the app starts without it, but AI endpoints will not function.

---

## 🛠 Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/ai-support-ticketing-backend.git
cd ai-support-ticketing-backend
```

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🗄 Database Setup

Run migrations:

```bash
alembic upgrade head
```

This creates the following tables:

```
users
refresh_tokens
tickets
ai_results
comments
alembic_version
```

---

## ▶️ Running the Server

```bash
uvicorn app.main:app --reload
```

Swagger UI → `http://127.0.0.1:8000/docs`

> Swagger docs are hidden when `ENV=production`.

---

## 🔐 Authentication Endpoints

### Register
```
POST /auth/register
```
```json
{
  "email": "user@example.com",
  "password": "Secure@1234"
}
```
Password must be at least 8 characters and include an uppercase letter, a number, and a special character.

---

### Login
```
POST /auth/login
```
Returns:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "abc123...",
  "token_type": "bearer"
}
```

---

### Refresh Token
```
POST /auth/refresh
```
```json
{ "refresh_token": "abc123..." }
```
Returns a new token pair. The old refresh token is revoked immediately (rotation).

---

### Logout
```
POST /auth/logout
```
```json
{ "refresh_token": "abc123..." }
```
Revokes the refresh token. Returns `204 No Content`.

---

### Current User
```
GET /auth/me
```
```
Authorization: Bearer <access_token>
```

---

## 🎫 Ticket Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/tickets/` | Create a ticket |
| `GET` | `/tickets/` | List tickets (own or all for admin) |
| `GET` | `/tickets/{id}` | Get ticket details |
| `PATCH` | `/tickets/{id}` | Update ticket |
| `POST` | `/tickets/{id}/close` | Close a ticket |
| `DELETE` | `/tickets/{id}` | Delete ticket (admin only) |

---

## 💬 Comment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/tickets/{id}/comments` | Add a comment |
| `GET` | `/tickets/{id}/comments` | List comments |
| `PATCH` | `/tickets/{id}/comments/{cid}` | Edit a comment |
| `DELETE` | `/tickets/{id}/comments/{cid}` | Delete a comment |

> Set `is_internal: true` to post agent-only notes (agents/admins only).

---

## 🤖 AI Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/classify/{ticket_id}` | Classify ticket (category, priority, summary) |
| `POST` | `/ai/draft/{ticket_id}` | Generate draft reply (agents/admins only) |
| `GET` | `/ai/results/{ticket_id}` | Get latest AI result |
| `GET` | `/ai/results/{ticket_id}/history` | Get full AI result history |

---

## 🔑 Roles

| Role | Capabilities |
|------|-------------|
| `USER` | Create tickets, comment on own tickets, view own data |
| `SUPPORT_AGENT` | View all tickets, post internal notes, classify, generate drafts |
| `ADMIN` | All of the above + delete tickets and comments |

Assign roles manually via DB for development:
```sql
UPDATE users SET role = 'SUPPORT_AGENT' WHERE email = 'agent@example.com';
UPDATE users SET role = 'ADMIN' WHERE email = 'admin@example.com';
```

---

## 🧪 Running Tests

Create the test database:
```bash
psql -U postgres -c "CREATE DATABASE ai_support_test_db;"
```

Run all tests:
```bash
pytest tests/ -v
```

Run a specific module:
```bash
pytest tests/test_auth.py -v
pytest tests/test_tickets.py -v
```

**63 tests — 0 failures.**

---


## 📄 License

MIT License