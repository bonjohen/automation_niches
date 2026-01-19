# SMB Compliance Automation Platform

A unified AI-driven compliance automation platform for small businesses (10-50 employees). Track vendor insurance certificates, manage compliance requirements, and automate expiration reminders.

## Features

- **Vendor Management**: Track vendors, contractors, and service providers
- **AI Document Processing**: Upload COIs and automatically extract key data using OCR + GPT-4
- **Compliance Tracking**: Monitor expiration dates and compliance status at a glance
- **Smart Notifications**: Automated email reminders before certificates expire
- **White-Label Ready**: Customize with your branding for property management or consulting use
- **Multi-Niche Platform**: COI tracking is the first "skin" - architecture supports fleet compliance, lease management, and more

## Tech Stack

### Backend
- **Framework**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Authentication**: JWT tokens
- **AI**: OpenAI GPT-4 for document extraction
- **OCR**: Tesseract (or Google Vision API)
- **Background Tasks**: Celery with Redis

### Frontend
- **Framework**: Next.js 14 with React 18
- **Styling**: Tailwind CSS with CSS variables for theming
- **State Management**: TanStack Query (React Query)
- **Forms**: React Hook Form with Zod validation

## Project Structure

```
automation_niches/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/    # FastAPI routes
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # Business logic
│   │   ├── ai/               # OCR + LLM pipeline
│   │   └── config/           # Settings, YAML loader
│   ├── migrations/           # Alembic migrations
│   ├── tests/                # Test suite
│   ├── main.py               # App entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   └── services/         # API client
│   └── package.json
├── configs/
│   └── niches/               # YAML niche configurations
│       └── coi_tracking.yaml
└── docs/
    ├── PROJECT_TODOS.md      # Task tracker
    ├── yaml_schema.md        # YAML config documentation
    ├── user_stories_coi_tracking.md
    └── competitor_analysis.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis (for background tasks)

### Backend Setup

1. **Clone and navigate to backend**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (especially DATABASE_URL and OPENAI_API_KEY)
   ```

5. **Create database**
   ```bash
   # Using psql
   createdb compliance_db

   # Or with PostgreSQL client
   psql -U postgres -c "CREATE DATABASE compliance_db;"
   ```

6. **Run migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the server**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

   The API will be available at http://localhost:8000
   - API docs: http://localhost:8000/api/docs
   - Health check: http://localhost:8000/health

### Frontend Setup

1. **Navigate to frontend**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env.local
   # Edit if needed (defaults work for local development)
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

   The app will be available at http://localhost:3000

## Configuration

### Niche Configuration (YAML)

The platform uses YAML files to define industry-specific configurations. See `docs/yaml_schema.md` for the full schema.

Example niche config location: `configs/niches/coi_tracking.yaml`

To validate a niche configuration:
```bash
cd backend
python -m app.config.yaml_validator configs/niches/coi_tracking.yaml
```

### Environment Variables

See `.env.example` files in both `backend/` and `frontend/` directories for all available configuration options.

Key settings:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key (generate a secure one for production)
- `OPENAI_API_KEY`: Required for AI document extraction
- `EMAIL_PROVIDER`: Set to `sendgrid` or `mailgun` for production emails

## Development

### Running Tests

Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm test
```

### Code Style

Backend (Python):
```bash
black app/
isort app/
ruff check app/
mypy app/
```

Frontend (TypeScript):
```bash
npm run lint
npm run type-check
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Create new account |
| `/api/v1/auth/login` | POST | Login and get JWT token |
| `/api/v1/auth/me` | GET | Get current user info |
| `/api/v1/entities` | GET/POST | List/create vendors |
| `/api/v1/entities/{id}` | GET/PATCH/DELETE | Vendor CRUD |
| `/api/v1/requirements` | GET/POST | List/create requirements |
| `/api/v1/requirements/summary` | GET | Compliance stats |
| `/api/v1/documents` | GET/POST | List/upload documents |
| `/api/v1/documents/{id}/process` | POST | Trigger AI extraction |
| `/api/v1/notifications` | GET | List notifications |

## Deployment

### Docker (Coming Soon)

```bash
docker-compose up -d
```

### Manual Deployment

1. Set up PostgreSQL and Redis
2. Configure environment variables
3. Run migrations: `alembic upgrade head`
4. Start with Gunicorn: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker`
5. Configure reverse proxy (nginx)

## Roadmap

- [x] Phase 1: Foundation & Architecture
- [ ] Phase 2: Backend Core Development
- [ ] Phase 3: AI Integration Pipeline
- [ ] Phase 4: Frontend Development
- [ ] Phase 5: CRM Integration
- [ ] Phase 6: Testing & Hardening
- [ ] Phase 7: Beta Launch

See `docs/PROJECT_TODOS.md` for detailed task tracking.

## Contributing

This is currently a private project. Contact the maintainer for contribution guidelines.

## License

Proprietary - All rights reserved.

---

Built with FastAPI, Next.js, and OpenAI
