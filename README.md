# AI Support Ticketing Backend

A production-style backend API for an AI-powered support ticketing system.

The system allows users to submit support tickets, which are automatically analyzed by AI to classify issues, determine urgency, and generate draft responses for support agents.

This project is being built incrementally using production-grade backend architecture.

---

# 🚀 Features

### Authentication System

* User registration
* Secure login with JWT
* Password hashing using Argon2
* Role-based access control (RBAC)

### Database Layer

* PostgreSQL
* SQLAlchemy ORM
* Alembic migration management

### Security

* JWT token authentication
* Secure password hashing
* Environment-based configuration

### Architecture

* Clean service-based architecture
* Separation of concerns
* Scalable project structure

---

# 🧰 Tech Stack

* Python 3.12+
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* JWT (python-jose)
* Passlib (Argon2 hashing)
* Pydantic
* OpenAI API *(planned)*
* Pytest *(planned)*



# ⚙️ Environment Setup

Create a `.env` file in the project root.

Example:

```
ENV=development

DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_support_db

SECRET_KEY=your_secret_key
ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

PASSWORD_HASH_SCHEME=argon2

OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=30
```

---

# 🛠 Installation

Clone the repository:

```
git clone https://github.com/yourusername/ai-support-ticketing-backend.git
cd ai-support-ticketing-backend
```

Create virtual environment:

```
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

---

# 🗄 Database Setup

Run migrations:

```
alembic upgrade head
```

This will create:

```
users
alembic_version
```

tables in PostgreSQL.

---

# 🔐 Authentication Endpoints

### Register

```
POST /auth/register
```

Example body:

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

---

### Login

```
POST /auth/login
```

Returns:

```json
{
  "access_token": "jwt_token",
  "token_type": "bearer"
}
```

---

### Current User

```
GET /auth/me
```

Header:

```
Authorization: Bearer <token>
```

---

# 🔑 Roles

Users have role-based access:

```
USER
SUPPORT_AGENT
ADMIN
```

Admins can be assigned manually through the database for development.

---

# 📌 Notes

* `.env` files are excluded from version control
* Passwords are securely hashed using Argon2
* JWT is used for stateless authentication
* API follows a service-layer architecture

---

# 🚧 Upcoming Features

* Support ticket management system
* AI ticket classification
* AI-generated response drafts
* Admin dashboard APIs
* Audit logging system
* Advanced RBAC
* Test suite with Pytest

---

# 📄 License

MIT License
