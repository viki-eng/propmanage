\# PropManage – Property Maintenance Management System



A mobile-first, full-stack web application for property maintenance management built with \*\*FastAPI\*\* (Python) and vanilla \*\*HTML/CSS/JavaScript\*\*.



\## 🏗 Architecture



```

Frontend (SPA)          Backend (REST API)          Database

HTML/CSS/JS  ────────►  FastAPI + SQLAlchemy  ────►  SQLite (async)

&nbsp;                        JWT Auth

&nbsp;                        File Uploads

```



\### Tech Stack

| Layer | Technology |

|-------|-----------|

| \*\*Backend\*\* | Python 3.12, FastAPI, SQLAlchemy (async), Pydantic v2 |

| \*\*Database\*\* | SQLite via aiosqlite (zero config, easily swappable) |

| \*\*Auth\*\* | JWT (python-jose) + bcrypt password hashing |

| \*\*Frontend\*\* | Vanilla HTML5, CSS3, JavaScript (ES6+) |

| \*\*File Storage\*\* | Local filesystem with UUID naming |



\### Key Design Decisions

\- \*\*Mobile-first responsive CSS\*\* – works seamlessly on phones, tablets, and desktops

\- \*\*Single-page application\*\* without a frontend framework for simplicity and performance

\- \*\*Async everything\*\* – FastAPI + async SQLAlchemy for non-blocking I/O

\- \*\*Role-based access control\*\* baked into API endpoints via dependency injection

\- \*\*Activity logging\*\* – every ticket action is recorded for full audit trail

\- \*\*In-app notifications\*\* – real-time-ready notification system



---



\## 👥 Roles \& Permissions



| Action | Tenant | Manager | Technician |

|--------|--------|---------|------------|

| Submit maintenance request | ✅ | ✅ | ❌ |

| View own tickets | ✅ | — | — |

| View all tickets | ❌ | ✅ | ❌ |

| View assigned tickets | — | — | ✅ |

| Assign technicians | ❌ | ✅ | ❌ |

| Change priority | ❌ | ✅ | ❌ |

| Update status | ❌ | ✅ | ✅ (own) |

| Upload images | ✅ | ✅ | ✅ |

| Delete tickets | ❌ | ✅ | ❌ |

| View notifications | ✅ | ✅ | ✅ |



---



\## 🔄 Status Flow



```

Open  →  Assigned  →  In Progress  →  Done

&nbsp; ↑         ↓              ↓            |

&nbsp; └─────────┘──────────────┘            |

&nbsp; └─────────────────────────────────────┘  (re-open)

```



---



\## 🚀 Quick Start



\### Prerequisites

\- Python 3.10+ installed



\### Setup



```bash

\# 1. Clone the repository

git clone <repo-url>

cd qwego



\# 2. Create and activate virtual environment

python -m venv venv

\# Windows:

venv\\Scripts\\activate

\# macOS/Linux:

source venv/bin/activate



\# 3. Install dependencies

pip install -r requirements.txt



\# 4. Seed the database with demo data

python seed\_data.py



\# 5. Run the application

python run.py

```



Open \*\*http://localhost:8000\*\* in your browser.



\### Demo Credentials



All passwords: `password123`



| Role | Email |

|------|-------|

| \*\*Manager\*\* | manager@propmanage.com |

| \*\*Tenant\*\* | tenant1@propmanage.com |

| \*\*Tenant\*\* | tenant2@propmanage.com |

| \*\*Tenant\*\* | tenant3@propmanage.com |

| \*\*Technician\*\* | tech1@propmanage.com |

| \*\*Technician\*\* | tech2@propmanage.com |



---



\## 🐳 Docker



```bash

docker-compose up --build

```



---



\## 📁 Project Structure



```

qwego/

├── backend/

│   ├── \_\_init\_\_.py

│   ├── main.py              # FastAPI app entry point

│   ├── config.py             # App configuration

│   ├── database.py           # Async SQLAlchemy setup

│   ├── models.py             # ORM models (User, Ticket, etc.)

│   ├── schemas.py            # Pydantic validation schemas

│   ├── auth.py               # JWT + password + role deps

│   └── routers/

│       ├── auth\_routes.py    # Login, register, profile

│       ├── tickets.py        # CRUD, assign, status, upload

│       ├── users.py          # List users/technicians

│       └── notifications.py  # List, read, mark all read

├── frontend/

│   ├── index.html            # Single-page app

│   ├── css/

│   │   └── styles.css        # Mobile-first responsive styles

│   └── js/

│       ├── api.js            # HTTP client module

│       ├── auth.js           # Login/register logic

│       ├── tickets.js        # Ticket CRUD + UI

│       ├── notifications.js  # Notification list + actions

│       └── app.js            # Navigation + orchestration

├── data/                     # SQLite database (auto-created)

├── uploads/                  # Uploaded images

├── seed\_data.py              # Demo data seeder

├── run.py                    # Dev server launcher

├── requirements.txt

├── Dockerfile

├── docker-compose.yml

└── README.md

```



---



\## 📡 API Endpoints



\### Authentication

| Method | Endpoint | Description |

|--------|----------|-------------|

| POST | `/api/auth/register` | Create new account |

| POST | `/api/auth/login` | Login, returns JWT |

| GET | `/api/auth/me` | Get current user profile |



\### Tickets

| Method | Endpoint | Description |

|--------|----------|-------------|

| GET | `/api/tickets/stats` | Dashboard statistics |

| GET | `/api/tickets/` | List tickets (role-filtered) |

| GET | `/api/tickets/{id}` | Ticket detail + activity log |

| POST | `/api/tickets/` | Create new ticket |

| PATCH | `/api/tickets/{id}` | Update ticket/status/assign |

| DELETE | `/api/tickets/{id}` | Delete ticket (manager only) |

| POST | `/api/tickets/{id}/images` | Upload images |



\### Users

| Method | Endpoint | Description |

|--------|----------|-------------|

| GET | `/api/users/` | List users (manager only) |

| GET | `/api/users/technicians` | List technicians |



\### Notifications

| Method | Endpoint | Description |

|--------|----------|-------------|

| GET | `/api/notifications/` | List user notifications |

| GET | `/api/notifications/unread-count` | Unread count |

| PATCH | `/api/notifications/{id}/read` | Mark as read |

| PATCH | `/api/notifications/read-all` | Mark all as read |



---



\## ✨ Features Implemented



\- ✅ JWT authentication with role-based access control

\- ✅ Three roles: Tenant, Manager, Technician

\- ✅ Ticket CRUD with validation

\- ✅ Status flow: Open → Assigned → In Progress → Done

\- ✅ Technician assignment by managers

\- ✅ Priority management (Low, Medium, High, Urgent)

\- ✅ Image upload with validation (type + size)

\- ✅ Activity log per ticket (full audit trail)

\- ✅ In-app notification system

\- ✅ Dashboard with statistics

\- ✅ Search and filter tickets

\- ✅ Mobile-first responsive design

\- ✅ Demo data seeding

\- ✅ Docker support

\- ✅ Clean, production-quality code structure



---



\## 🧪 Edge Cases Handled



\- Invalid status transitions are blocked

\- Tenants can only edit their own open tickets

\- Technicians can only update status on their assigned tickets

\- File upload validates extension and size limits

\- Email uniqueness enforced at DB level

\- Proper error messages returned for all failure cases

\- Token expiry and unauthorized access handled gracefully



---



\*\*Built with ❤️ for PropTech\*\*



