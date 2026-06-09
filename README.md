# Lai - Legal Document Intelligence System

A contract analysis platform that surfaces the critical 10% of a contract requiring human legal decisions while handling the other 90% automatically.

## Features

- **Document Ingestion** - Upload contracts in PDF or DOCX. Extracts and structures text preserving clause hierarchy, section numbering, and cross-references.
- **Clause Extraction** - Identifies and extracts named clauses: indemnity, limitation of liability, governing law, termination, IP ownership, payment terms, confidentiality.
- **Market Standard Comparison** - Compares extracted clauses against a configurable market-standard baseline. Flags deviations as favourable, unfavourable, or unusual.
- **Risk Scoring** - Assigns a risk score to each flagged clause and an overall contract risk score. Categorises by type: financial, operational, legal, reputational.
- **Plain-English Summary** - Generates a 1-page executive summary: what it covers, who carries the risk, key commercial terms, and top 3 issues to negotiate.
- **Clause Comparison** - Side-by-side comparison of the same clause across multiple contracts for due-diligence scenarios.
- **Contract Chat** - Ask questions about your contract with citations to specific clauses and sections.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vite + React 19 + TypeScript + Tailwind CSS v4 |
| Backend | Python FastAPI |
| Database | PostgreSQL |
| Document Parsing | IBM Docling (PDF/DOCX) |
| AI/LLM | Google Gemini 3.5 Flash |
| Charts | Recharts |

## Project Structure

```
Lai/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py       # FastAPI app entry
│   │   ├── config.py     # Settings
│   │   ├── database.py   # SQLAlchemy setup
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── routers/      # API endpoints
│   │   ├── services/     # Business logic (parser, extractor, scorer, etc.)
│   │   └── baselines/    # Market-standard clause definitions
│   └── pyproject.toml
├── frontend/             # React SPA
│   ├── src/
│   │   ├── pages/        # Dashboard, Upload, Contract, Compare, Chat
│   │   ├── components/   # Layout and shared components
│   │   └── lib/          # API client, utilities
│   └── package.json
├── docker-compose.yml    # PostgreSQL for local dev
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker (for PostgreSQL)
- Google Gemini API key

### 1. Clone and setup

```bash
git clone https://github.com/mist-ic/Lai.git
cd Lai
```

### 2. Start the database

```bash
docker compose up -d
```

### 3. Backend setup

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e .

# Create .env file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the backend
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

### 4. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at http://localhost:5173

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/contracts/upload | Upload a PDF/DOCX contract |
| GET | /api/contracts | List all contracts |
| GET | /api/contracts/{id} | Get contract with clauses |
| POST | /api/contracts/{id}/analyze | Trigger AI analysis |
| GET | /api/contracts/{id}/status | Check analysis progress |
| GET | /api/contracts/{id}/clauses | Get extracted clauses |
| GET | /api/contracts/{id}/summary | Get executive summary |
| POST | /api/contracts/{id}/chat | Ask questions about contract |
| POST | /api/compare | Compare clauses across contracts |
| GET | /api/baselines | Get market-standard baselines |

## How It Works

1. **Upload** - Drop a PDF or DOCX contract
2. **Parse** - IBM Docling extracts text with structure preservation
3. **Extract** - Gemini 3.5 Flash identifies all clause types using structured JSON output
4. **Score** - Hybrid scoring: rule-based heuristics (pattern matching) + LLM risk assessment
5. **Summarize** - AI generates a plain-English executive summary
6. **Review** - Interactive dashboard with risk gauge, radar charts, and expandable clause cards

## Team

Group assignment - 5 members.

## License

MIT
