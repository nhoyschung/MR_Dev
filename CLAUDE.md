# MR-System: Vietnam Real Estate Market Research

## Overview
Market research system for Vietnam real estate that ingests NHO-PD analysis reports, stores structured data in SQLite, and provides market intelligence via Claude Code sub-agents and slash commands. Modeled after 11 NHO-PD reports (1,200+ pages) covering HCMC, Hanoi, and Binh Duong markets.

## Tech Stack
- **Language**: Python 3.12+
- **ORM**: SQLAlchemy 2.x (declarative mapping)
- **Database**: SQLite (file: `data/mr_system.db`)
- **Validation**: Pydantic 2.x
- **PDF Parsing**: PyMuPDF (fitz)
- **Templates**: Jinja2
- **Testing**: pytest

## Project Structure
```
MR-system/
├── src/                    # Application source code
│   ├── config.py           # Paths, DB URL, constants
│   ├── db/                 # Database layer
│   │   ├── connection.py   # Engine, session factory
│   │   ├── models.py       # SQLAlchemy models (20 tables)
│   │   ├── init_db.py      # Create tables + seed reference data
│   │   └── queries.py      # Common query helpers
│   ├── seeders/            # Data seeding pipeline
│   │   ├── base_seeder.py  # Abstract seeder with validation
│   │   ├── *_seeder.py     # Individual table seeders
│   │   └── run_all.py      # Orchestrator (dependency order)
│   └── utils/              # Shared utilities
│       └── text_parser.py  # PDF text extraction helpers
├── data/
│   ├── seed/               # JSON seed files
│   └── mr_system.db        # SQLite database (generated)
├── templates/              # Jinja2 report templates
├── tests/                  # pytest test suite
├── user_resources/         # Source PDFs + extracted text
└── docs/                   # Design documents
```

## Coding Standards
- All code and comments in **English**
- Type hints on all function signatures
- Pydantic models for data validation at boundaries
- SQLAlchemy 2.x declarative style with `Mapped[]` and `mapped_column()`
- snake_case for variables/functions, PascalCase for classes

## Database Conventions
- Table names: lowercase plural (e.g., `cities`, `projects`)
- Primary keys: `id` (Integer, autoincrement)
- Foreign keys: `{table_singular}_id` (e.g., `city_id`, `project_id`)
- Timestamps: `created_at`, `updated_at` where needed
- Soft deletes not used; hard deletes only

## Key Commands
```bash
pip install -r requirements.txt       # Install dependencies
python -m src.db.init_db              # Create tables
python -m src.seeders.run_all         # Seed all data
pytest tests/ -v                      # Run tests
```

## Agent Architecture
- `.claude/agents/data-extractor.md` — Extracts structured data from PDF text
- `.claude/agents/market-analyzer.md` — Database queries for market analysis
- `.claude/agents/competitor-benchmarker.md` — 11-dimension competitive analysis

## Slash Commands
- `/vn-market-briefing` — Market overview for city/period
- `/project-profile` — Deep dive on a project
- `/competitor-compare` — Side-by-side project comparison
- `/zone-analysis` — District supply-demand analysis
- `/price-check` — Price lookup with grade context
- `/db-query` — Direct database query interface
