CyChat is a real-time chat application with end-to-end encryption, built with FastAPI and vanilla JavaScript.

## What's This?

Cychat is a self-hosted messaging platform that supports:

- **Direct messaging** between users
- **Group chat rooms** for team conversations
- **End-to-end encryption** using ECDH key exchange and AES-256-GCM
- **File sharing** (images, documents, archives, etc.)
- **Real-time updates** via WebSockets
- **Contact management**

The backend runs on FastAPI with SQL Server, and the frontend is plain HTML/CSS/JavaScript—no build step required.
<img width="1582" height="857" alt="Design_Architecture" src="https://github.com/user-attachments/assets/fdaecb0e-4dc1-4471-97d5-1b1b2d8575e0" />
<img width="1217" height="755" alt="Database_Design" src="https://github.com/user-attachments/assets/160472cd-906f-4ee9-8657-7ccc0e928db2" />

## Tech Stack

**Backend:**
- Python 3.11+ with FastAPI
- SQLAlchemy (async) for database access
- SQL Server
- JWT authentication with bcrypt password hashing
- Prometheus metrics built-in

**Frontend:**
- Vanilla JavaScript (no frameworks)
- Web Crypto API for E2E encryption
- WebSocket for real-time messaging

## Quick Start

### 1. Clone and set up the environment

```powershell
cd E:\Chat_Project\Updates_Things

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure the app

Copy the template and edit as needed:

```powershell
copy env_config_template.txt .env
```

The defaults work for local SQL Server Express with Windows Authentication. Change `JWT_SECRET_KEY` to something secure.

### 3. Set up the database

Create a database called `ChatDB` in SQL Server. The app creates all tables automatically on startup.

```sql
CREATE DATABASE ChatDB;
```

### 4. Run it

```powershell
python -m app
```

The server starts at `http://localhost:8000`. API docs are at `/docs` when running in debug mode.

### 5. Open the frontend

Navigate to `Cychat_frontend/` and open `login.html` in your browser. Or serve it locally:

```powershell
cd Cychat_frontend
python -m http.server 5500
```

Then go to `http://localhost:5500/login.html`.

## Project Structure

```
├── app/
│   ├── auth/          # Login, registration, JWT handling
│   ├── users/         # User profiles and settings
│   ├── contacts/      # Contact list management
│   ├── chats/         # Direct messages
│   ├── rooms/         # Group chat rooms
│   ├── web_sockets/   # Real-time message handling
│   ├── utils/         # Crypto, database helpers, pub/sub
│   └── config.py      # App configuration
├── Cychat_frontend/
│   ├── login.html
│   ├── register.html
│   ├── chat.html      # Main chat interface
│   ├── profile.html
│   └── static/js/
│       └── e2e-crypto.js   # Client-side encryption
├── uploads/           # User-uploaded files
└── requirements.txt
```

## End-to-End Encryption

Messages between users are encrypted client-side before leaving the browser:

1. Each user generates an ECDH P-256 key pair on first login
2. Public keys are stored on the server and exchanged between contacts
3. A shared secret is derived using ECDH
4. Messages are encrypted with AES-256-GCM using a random IV

The server never sees plaintext message content.

Room encryption works similarly—a symmetric room key is generated when creating the room, then encrypted and shared with each member using their public key.

## API Overview

| Endpoint | What it does |
|----------|--------------|
| `POST /api/v1/auth/register` | Create account |
| `POST /api/v1/auth/login` | Get access token |
| `GET /api/v1/user/profile` | Current user info |
| `POST /api/v1/contact` | Add a contact |
| `GET /api/v1/contacts` | List contacts |
| `POST /api/v1/message` | Send a message |
| `GET /api/v1/conversation?receiver=email` | Get chat history |
| `POST /api/v1/room` | Create/join a room |
| `GET /api/v1/rooms` | List your rooms |
| `ws://localhost:8000/api/v1/ws/chat/{sender}/{receiver}` | Direct chat socket |
| `ws://localhost:8000/api/v1/ws/{sender}/{room}` | Room chat socket |

Full documentation available at `/docs` when `DEBUG=info`.

## Configuration

All settings go in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_TYPE` | `sqlserver` | Database type (`sqlserver` or `mysql`) |
| `DB_HOST` | `localhost\SQLEXPRESS` | Database server |
| `DB_NAME` | `ChatDB` | Database name |
| `DB_USERNAME` | (empty) | Leave empty for Windows Auth |
| `DB_PASSWORD` | (empty) | Leave empty for Windows Auth |
| `JWT_SECRET_KEY` | (change this!) | Secret for signing tokens |
| `DEBUG` | `info` | Set to empty string for production |
| `CORS_ORIGINS` | (see template) | Allowed frontend origins |

## Requirements

- Python 3.11+
- SQL Server with ODBC Driver 17
- A modern browser with Web Crypto API support

## Troubleshooting

**"ODBC Driver not found"**
Install [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).

**"Cannot open database"**
Create the database first: `CREATE DATABASE ChatDB;`

**CORS errors on frontend**
Add your frontend URL to `CORS_ORIGINS` in `.env`. If opening HTML files directly, include `file://`.
