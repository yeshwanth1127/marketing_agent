# Marketing Intelligence Pipeline

A deterministic marketing intelligence factory powered by AI reasoning nodes.

## 🎯 Overview

This system transforms raw marketing data into actionable insights, strategies, and creative content through a systematic pipeline:

**Data → Normalize → Store → Agents Analyze → Agents Decide → Agents Generate → Aggregate → Human Approves**

## 🏗️ Architecture

See [guide.md](./guide.md) for the complete system architecture, tech stack, and implementation details.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

### Setup

1. **Clone and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services with Docker:**
   ```bash
   docker-compose up -d
   ```

   This starts:
   - PostgreSQL on port 5432
   - Qdrant vector DB on port 6333
   - API server on port 8000

4. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start the API server:**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📁 Project Structure

```
marketing_agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models
│   │   ├── campaign.py
│   │   ├── metrics.py
│   │   └── agent.py
│   ├── routers/             # API endpoints
│   │   ├── agent.py
│   │   ├── campaigns.py
│   │   └── metrics.py
│   └── services/            # Business logic
│       ├── agent_service.py
│       ├── analytics_agent.py
│       ├── strategist_agent.py
│       ├── content_agent.py
│       └── aggregator.py
├── alembic/                 # Database migrations
├── guide.md                 # Complete system guide
├── requirements.txt
├── docker-compose.yml
└── Dockerfile
```

## 🔄 System Flow

1. **Data Ingestion** (n8n workflows)
   - Pull data from Meta Ads API
   - Pull data from GA4 API
   - Normalize and store in PostgreSQL

2. **Agent Execution** (API trigger)
   - Analytics Agent analyzes performance
   - Strategist Agent makes decisions
   - Content Agent generates creatives
   - Aggregator combines outputs

3. **Human Review**
   - Review insights, actions, and creatives
   - Approve/reject recommendations
   - Execute approved actions

## 📊 API Endpoints

### Agent
- `POST /api/agent/run-weekly` - Trigger weekly analysis
- `GET /api/agent/runs/{run_id}` - Get run details
- `GET /api/agent/runs` - List runs

### Campaigns
- `GET /api/campaigns` - List campaigns
- `GET /api/campaigns/{campaign_id}` - Get campaign details

### Metrics
- `GET /api/metrics/daily` - Get daily metrics
- `GET /api/metrics/weekly` - Get weekly metrics

## 🛠️ Development

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
pytest
```

## 📝 Next Steps

1. Set up n8n workflows for data ingestion
2. Configure Meta Ads and GA4 API credentials
3. Populate brand knowledge base (Qdrant)
4. Implement LangGraph state machine
5. Add RAG integration for brand compliance
6. Set up monitoring and logging

## 📚 Documentation

- [Complete System Guide](./guide.md)
- [API Documentation](http://localhost:8000/docs)

## 🔒 Security Notes

- Never commit `.env` file
- Use strong secrets in production
- Configure CORS appropriately
- Use OAuth for API integrations

## 📄 License

[Your License Here]
