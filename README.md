# JanSahayak AI - Backend API & Database Service
**Member 2 Role: Backend Lead & Database Architect**

This repository contains the high-performance asynchronous REST API backend for **JanSahayak AI (ಜನಸಹಾಯಕ AI)** — built with FastAPI, MongoDB (Motor/PyMongo), and secure JWT authentication.

---

## 👨‍💻 Member 2 Responsibilities & Modules Built

1. **FastAPI Application Architecture (`app/main.py`, `app/config.py`)**:
   - Asynchronous application lifecycle with automatic MongoDB initialization and verified database seeding.
   - CORS middleware enabled for seamless frontend communication.
   - Structured environment configuration with Pydantic settings.

2. **Authentication & Security Engine (`app/services/auth_service.py`, `app/middleware/auth_middleware.py`)**:
   - Salted PBKDF2-HMAC-SHA256 password hashing.
   - Signed JSON Web Token (JWT) generation and verification.
   - Role-Based Access Control (RBAC) middleware distinguishing `citizen` and `admin` permissions.

3. **Database Integration (`app/services/database.py`)**:
   - Asynchronous MongoDB connection using Motor and PyMongo (`mongodb://127.0.0.1:27017/jansahayak`).
   - Resilient in-memory fallback store to ensure zero API crashes if MongoDB service is restarting.
   - Pre-seeding service for demo citizen and admin credentials (`app/services/seed_data.py`).

4. **REST API Route Handlers (`app/routes/`)**:
   - `POST /api/auth/register` — Citizen/Admin account creation.
   - `POST /api/auth/login` — JWT token acquisition.
   - `GET /api/auth/me` — Current authenticated session user.
   - `GET /api/profile` — Fetch citizen socio-economic details.
   - `POST /api/profile` / `PUT /api/profile` — Save/update citizen profile.
   - `GET /api/schemes` — Catalog of government schemes with category/state filters.
   - `GET /api/schemes/{id}` — Scheme dossier details.
   - `POST /api/eligibility/check` — Rule evaluation integration.
   - `POST /api/rag/ask` — AI RAG Chatbot query handler.
   - `POST /api/admin/documents/upload` — Admin document upload handler.
   - `POST /api/admin/documents/ingest` — Full knowledge store re-indexer.
   - `GET /api/health` — System status and vectorstore metrics.

---

## 🛠 Tech Stack
- **Framework**: Python 3.10+, FastAPI, Uvicorn
- **Validation**: Pydantic v2, Pydantic-Settings
- **Database**: MongoDB (Motor async driver & PyMongo)
- **Security**: PyJWT, Salted PBKDF2 / Bcrypt

---

## 🚀 How to Run Locally

### 1. Create and Activate Virtual Environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Ensure MongoDB is running locally (`mongodb://127.0.0.1:27017/jansahayak`).

### 4. Start API Server
```bash
uvicorn app.main:app --reload --port 8000
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger Documentation: `http://127.0.0.1:8000/docs`

---

## 📦 How to Push This Part to Your GitHub Repository

```bash
# 1. Initialize git in this directory
git init

# 2. Add all files
git add .

# 3. Create your first commit
git commit -m "feat: complete JanSahayak AI backend API with FastAPI, MongoDB & JWT auth"

# 4. Set branch to main
git branch -M main

# 5. Connect your remote GitHub repository (Replace with your actual repo URL)
git remote add origin https://github.com/<your-username>/jansahayak-backend.git

# 6. Push to GitHub
git push -u origin main
```
