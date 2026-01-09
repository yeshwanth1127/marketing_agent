Marketing Intelligence Pipeline - Implementation Guide

System Overview

This is a deterministic marketing intelligence factory powered by AI reasoning nodes. It is NOT a chatbot or magic AI—it's a systematic pipeline that transforms raw marketing data into actionable insights, strategies, and creative content.

### Core Principle
> Pipelines pull data → Normalize → Store → Agents analyze → Agents decide → Agents generate → Aggregate → Human approves

---

##  System Architecture: 5 Layers

### Layer 1: Data Source Layer (Reality Layer)
Purpose: Collect ground-truth business data from marketing platforms

Sources (MVP):
- Google Analytics 4 (GA4) - website traffic & conversions
- Meta Ads (Facebook/Instagram) - ad performance
- *(Optional later)* CRM integration

Implementation:
- Official platform APIs only (no scraping)
- OAuth authentication (one-time client connection)
- No CSV uploads or manual imports

Output Format:
```json
{
  "campaign": "Campaign_X",
  "date": "2026-01-08",
  "spend": 1200.00,
  "clicks": 340,
  "conversions": 12,
  "revenue": 9000.00,
  "impressions": 50000,
  "source": "meta_ads"
}
```

---

### Layer 2: Orchestration & Ingestion Layer (n8n)
**Purpose:** Automate data collection with reliability and error handling

**Responsibilities:**
- Scheduled data pulls (daily/weekly)
- API pagination handling
- Rate limit management
- OAuth token refresh
- Retry logic for failed requests
- Data cleaning and field mapping
- Database writes (upserts)

**Example n8n Workflows:**

**Workflow A: Meta Ads → Database**
```
Cron Trigger (Daily 2 AM)
  → Get Access Token (OAuth Refresh)
  → Get All Campaigns
  → For Each Campaign:
      → Get Campaign Insights (date range)
      → Normalize Data Fields
      → Upsert to daily_metrics table
  → Log Success/Failures
```

**Workflow B: GA4 → Database**
```
Cron Trigger (Daily 3 AM)
  → Authenticate GA4 API
  → Get Report (sessions, conversions, revenue)
  → Transform GA4 format → Canonical format
  → Upsert to daily_metrics table
  → Log Completion
```

**Why n8n?**
- Visual workflow builder
- Built-in API connectors
- Error handling and retries
- Scheduling without cron complexity
- Can run on-premise or cloud

---

### Layer 3: Data & Truth Layer (PostgreSQL)
**Purpose:** Single source of truth for all marketing data

**Why Agents Never Talk to APIs Directly:**
-  Deterministic (same data every time)
-  Fast (no API latency)
-  Testable (can mock DB easily)
-  Cheap (no API rate limits)
-  Reliable (data persists)

**Database Schema (MVP):**

#### `campaigns`
```sql
CREATE TABLE campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(500) NOT NULL,
  source VARCHAR(50) NOT NULL, -- 'meta_ads', 'ga4', etc.
  status VARCHAR(50), -- 'active', 'paused', 'archived'
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `daily_metrics`
```sql
CREATE TABLE daily_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date DATE NOT NULL,
  campaign_id UUID REFERENCES campaigns(id),
  source VARCHAR(50) NOT NULL,
  impressions BIGINT DEFAULT 0,
  clicks INTEGER DEFAULT 0,
  spend DECIMAL(12, 2) DEFAULT 0,
  conversions INTEGER DEFAULT 0,
  revenue DECIMAL(12, 2) DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(date, campaign_id, source)
);
```

#### `weekly_metrics` (Aggregated view)
```sql
CREATE TABLE weekly_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  week_start DATE NOT NULL,
  campaign_id UUID REFERENCES campaigns(id),
  source VARCHAR(50) NOT NULL,
  impressions BIGINT,
  clicks INTEGER,
  spend DECIMAL(12, 2),
  conversions INTEGER,
  revenue DECIMAL(12, 2),
  roas DECIMAL(10, 4), -- revenue / spend
  ctr DECIMAL(10, 4), -- clicks / impressions
  cpc DECIMAL(10, 4), -- spend / clicks
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(week_start, campaign_id, source)
);
```

#### `agent_runs`
```sql
CREATE TABLE agent_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_type VARCHAR(50) NOT NULL, -- 'weekly', 'daily', 'ad_hoc'
  status VARCHAR(50) NOT NULL, -- 'running', 'completed', 'failed'
  started_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  input_params JSONB,
  output JSONB,
  error_message TEXT
);
```

#### `insights`
```sql
CREATE TABLE insights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_run_id UUID REFERENCES agent_runs(id),
  insight_type VARCHAR(50) NOT NULL, -- 'drop', 'spike', 'opportunity', 'anomaly'
  campaign_id UUID REFERENCES campaigns(id),
  metric VARCHAR(50) NOT NULL,
  change_percent DECIMAL(10, 2),
  description TEXT,
  severity VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### `actions`
```sql
CREATE TABLE actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_run_id UUID REFERENCES agent_runs(id),
  action_type VARCHAR(50) NOT NULL, -- 'scale', 'pause', 'test', 'fix', 'optimize'
  campaign_id UUID REFERENCES campaigns(id),
  description TEXT,
  priority VARCHAR(20), -- 'low', 'medium', 'high'
  status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'executed'
  approved_by VARCHAR(255),
  approved_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### `creatives`
```sql
CREATE TABLE creatives (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_run_id UUID REFERENCES agent_runs(id),
  action_id UUID REFERENCES actions(id),
  platform VARCHAR(50) NOT NULL, -- 'meta', 'google', etc.
  creative_type VARCHAR(50), -- 'ad_copy', 'image_ad', 'video_ad'
  headline TEXT,
  primary_text TEXT,
  description TEXT,
  call_to_action VARCHAR(100),
  status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'approved', 'rejected', 'published'
  approved_by VARCHAR(255),
  approved_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

### Layer 4: Brand Brain (RAG Knowledge Layer)
**Purpose:** Ensure all outputs are on-brand and compliant

**Storage:** Vector Database (Qdrant or Pinecone)

**Content Stored:**
- Brand guidelines (voice, tone, style)
- Ideal Customer Profile (ICP) descriptions
- Product information and features
- Compliance rules and forbidden claims
- Past winning ad creatives (for reference)
- Competitor analysis (optional)

**How It Works:**
- All content is embedded and stored as vectors
- Every agent prompt includes RAG context:
  > "You MUST follow the brand knowledge retrieved from the knowledge base. Reject any ideas that violate brand guidelines or compliance rules."

**Implementation:**
- Use LangChain's vector store integration
- Embed documents using OpenAI embeddings or similar
- Retrieve relevant context before each agent reasoning step

---

### Layer 5: AI Reasoning Layer (LangGraph)
**Purpose:** The core decision-making engine

**Architecture:** Deterministic State Machine (NOT free-form agents)

**State Machine Flow:**
```
START
  ↓
CollectData (from DB)
  ↓
Analyze (Analytics Agent)
  ↓
Decide (Strategist Agent)
  ↓
Create (Content Agent)
  ↓
Aggregate (Combine all outputs)
  ↓
DONE
```

**Key Principles:**
- Each node has strict input/output JSON schemas
- All state transitions are logged
- Every run is debuggable and replayable
- No randomness in execution flow

---

## 🤖 The 3 MVP Agents

### Agent 1: Analytics Agent (Understanding)
**Role:** Analyze performance data and identify patterns

**Input:**
- Date range (last 7/14/30 days)
- Campaign metrics from database
- Comparison periods (week-over-week, month-over-month)

**Processing:**
- Calculate key metrics (ROAS, CTR, CPC, conversion rate)
- Compare periods to identify:
  - Performance drops
  - Performance spikes
  - Outliers and anomalies
  - Trends (improving/declining)
- Statistical analysis (z-scores, percentiles)

**Output Schema:**
```json
{
  "insights": [
    {
      "type": "drop",
      "campaign_id": "uuid",
      "campaign_name": "Campaign A",
      "metric": "ROAS",
      "current_value": 2.5,
      "previous_value": 3.7,
      "change_percent": -32.4,
      "severity": "high",
      "description": "ROAS dropped 32% week-over-week"
    },
    {
      "type": "opportunity",
      "campaign_id": "uuid",
      "campaign_name": "Campaign B",
      "metric": "CTR",
      "current_value": 3.2,
      "previous_value": 2.1,
      "change_percent": 48.3,
      "severity": "medium",
      "description": "CTR increased 48% - scaling opportunity"
    }
  ],
  "summary": "Identified 3 performance drops and 2 opportunities across 12 campaigns"
}
```

---

### Agent 2: Strategist Agent (Deciding)
**Role:** Make strategic decisions based on insights

**Input:**
- Insights JSON from Analytics Agent
- Budget constraints and rules
- Brand constraints from RAG
- Current campaign statuses

**Processing:**
- Prioritize insights by severity and impact
- Decide actions:
  - **Scale:** Increase budget for winners
  - **Pause:** Stop underperformers
  - **Fix:** Address specific issues (landing page, targeting, etc.)
  - **Test:** Propose new experiments
- Apply guardrails:
  - Max budget change limits
  - Minimum performance thresholds
  - Brand compliance checks

**Output Schema:**
```json
{
  "actions": [
    {
      "type": "scale",
      "campaign_id": "uuid",
      "campaign_name": "Campaign B",
      "description": "Increase budget by 30% due to strong CTR and ROAS",
      "priority": "high",
      "parameters": {
        "budget_change_percent": 30,
        "reason": "48% CTR increase, ROAS above 3.0"
      }
    },
    {
      "type": "test",
      "campaign_id": "uuid",
      "campaign_name": "Campaign C",
      "description": "Test new hook for audience segment X",
      "priority": "medium",
      "parameters": {
        "test_type": "creative_variant",
        "hypothesis": "Different hook will improve CTR for cold audience"
      }
    },
    {
      "type": "fix",
      "campaign_id": "uuid",
      "campaign_name": "Campaign A",
      "description": "Landing page mismatch causing low conversion rate",
      "priority": "high",
      "parameters": {
        "issue": "landing_page_mismatch",
        "recommended_fix": "Update landing page to match ad creative messaging"
      }
    }
  ],
  "summary": "Recommended 2 scaling actions, 1 test, and 1 fix"
}
```

---

### Agent 3: Content Agent (Producing)
**Role:** Generate creative content for tests and new campaigns

**Input:**
- Action list from Strategist Agent
- Brand Brain context (RAG retrieval)
- Past winning creatives
- Platform-specific requirements

**Processing:**
- For each "test" action, generate creative variants
- Follow brand guidelines strictly
- Reference past winners for inspiration
- Ensure compliance (no forbidden claims)
- Platform-specific formatting (Meta vs Google)

**Output Schema:**
```json
{
  "creatives": [
    {
      "action_id": "uuid",
      "platform": "meta",
      "creative_type": "ad_copy",
      "headline": "Transform Your Business in 30 Days",
      "primary_text": "Join 10,000+ companies using our platform to increase revenue by 40%. See results in your first month or money back.",
      "description": "Trusted by leading companies worldwide",
      "call_to_action": "Learn More",
      "target_audience": "B2B decision makers, 35-55, tech industry",
      "rationale": "Based on winning creative pattern: benefit-focused headline + social proof + risk reversal"
    }
  ],
  "summary": "Generated 3 creative variants for testing"
}
```

---

##  Result Aggregation Layer

**Purpose:** Combine all agent outputs into a single executive package

**Aggregator Node:**
- Takes insights, actions, and creatives
- Formats for human consumption
- Creates executive summary
- Structures for different outputs (Slack, Dashboard, PDF)

**Output Format:**
```json
{
  "run_id": "uuid",
  "run_date": "2026-01-08",
  "summary": "Performance declined in Campaign A (ROAS -32%), strong opportunity in Campaign B (CTR +48%). Recommended scaling Campaign B, fixing Campaign A landing page, and testing new creative for Campaign C.",
  "insights": [...],
  "actions": [...],
  "creatives": [...],
  "metrics": {
    "total_campaigns_analyzed": 12,
    "insights_found": 5,
    "actions_recommended": 4,
    "creatives_generated": 3
  }
}
```

---

##  Full MVP Pipeline Flow

```
1. n8n Cron Trigger (Weekly, Monday 9 AM)
   ↓
2. n8n pulls latest data from Meta Ads & GA4 APIs
   ↓
3. Data normalized and upserted to PostgreSQL
   ↓
4. n8n calls API: POST /api/agent/run-weekly
   ↓
5. LangGraph State Machine Starts:
   ├─→ CollectData Node (queries DB for last 30 days)
   ├─→ Analyze Node (Analytics Agent)
   ├─→ Strategy Node (Strategist Agent)
   ├─→ Creative Node (Content Agent)
   └─→ Aggregate Node (combines outputs)
   ↓
6. Result JSON stored in agent_runs table
   ↓
7. n8n receives result, formats and sends to:
   ├─→ Slack channel (summary + actions)
   ├─→ Dashboard (full report)
   └─→ (Optional) Email to stakeholders
   ↓
8. Human reviews and approves actions
   ↓
9. (Future) Approved actions executed via API
```

---

##  Human-in-the-Loop Control

**Critical Principle:** Nothing auto-publishes or auto-spends

**Approval Workflow:**
1. All actions marked as `status: 'pending'`
2. Human reviews in dashboard or Slack
3. Approve/reject individual actions
4. Approved actions can be executed (manually or via API)
5. Full audit trail of all decisions

**What Requires Approval:**
- Budget changes (scale/pause actions)
- New creative launches
- Campaign modifications
- Any spend-related changes

---

##  MVP Guardrails

### 1. JSON Schema Validation
- Every agent output validated against strict JSON schema
- Invalid outputs trigger retry or error state
- Prevents malformed data from propagating

### 2. Forbidden Words List
- Brand-specific forbidden terms
- Compliance-restricted claims
- Auto-rejection of content containing forbidden words

### 3. Brand Compliance Check
- Every creative checked against brand guidelines
- RAG retrieval ensures context-aware compliance
- Violations flagged before approval

### 4. Budget Change Limits
- Max budget increase: 50% per week (configurable)
- Max budget decrease: 100% (pause allowed)
- Requires explicit approval for changes > 25%

### 5. Audit Logging
- Every agent run logged with full state
- All state transitions recorded
- Input/output snapshots for debugging
- User actions (approvals/rejections) logged

---

##  Tech Stack

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI (REST API)
- **AI Framework:** LangGraph (state machine)
- **LLM:** OpenAI GPT-4 (or Anthropic Claude)
- **Vector DB:** Qdrant (or Pinecone)
- **Embeddings:** OpenAI text-embedding-3-small

### Database
- **Primary DB:** PostgreSQL 15+
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic

### Orchestration
- **Workflow Engine:** n8n (self-hosted or cloud)
- **Scheduling:** n8n cron triggers

### APIs & Integrations
- **Meta Ads API:** Facebook Marketing API
- **GA4 API:** Google Analytics Data API
- **OAuth:** Platform-specific OAuth flows

### Infrastructure (MVP)
- **Deployment:** Docker containers
- **Environment:** Development local, Production TBD
- **Secrets:** Environment variables (later: Vault)

### Monitoring & Logging
- **Logging:** Python logging + structured logs
- **Monitoring:** (Future) Prometheus + Grafana

---

##  Implementation Steps

### Phase 1: Foundation (Week 1)
1.  Project structure setup
2.  Database schema design and migrations
3.  FastAPI skeleton with basic endpoints
4.  PostgreSQL connection and models
5.  Environment configuration

### Phase 2: Data Layer (Week 2)
1.  Database models (SQLAlchemy)
2.  Data ingestion scripts (manual testing)
3.  n8n workflow setup (Meta Ads API)
4.  n8n workflow setup (GA4 API)
5.  Data validation and normalization

### Phase 3: Brand Brain (Week 2-3)
1.  Qdrant setup and connection
2.  Document embedding pipeline
3.  RAG retrieval functions
4.  Brand knowledge base population

### Phase 4: AI Agents (Week 3-4)
1.  LangGraph state machine setup
2.  Analytics Agent implementation
3.  Strategist Agent implementation
4.  Content Agent implementation
5.  Aggregator Node implementation

### Phase 5: Integration (Week 4-5)
1.  API endpoints for agent runs
2.  n8n → API integration
3.  Output formatting (Slack, Dashboard)
4.  Error handling and retries

### Phase 6: Guardrails & Polish (Week 5-6)
1.  JSON schema validation
2.  Compliance checks
3.  Audit logging
4.  Human approval workflow
5.  Testing and debugging

### Phase 7: MVP Launch (Week 6)
1.  End-to-end testing
2.  Documentation
3.  Deployment preparation
4.  First production run

---

##  Data Flow Diagram

```
┌─────────────┐
│  Meta Ads   │
│     API     │
└──────┬──────┘
       │
       │ OAuth + API Calls
       ↓
┌─────────────┐
│     n8n     │
│  Workflows  │
└──────┬──────┘
       │
       │ Normalized Data
       ↓
┌─────────────┐
│ PostgreSQL  │
│  Database   │
└──────┬──────┘
       │
       │ Query Metrics
       ↓
┌─────────────┐      ┌─────────────┐
│  LangGraph  │◄─────│   Qdrant    │
│ State Mach. │      │  (Brand DB) │
└──────┬──────┘      └─────────────┘
       │
       │ Agent Outputs
       ↓
┌─────────────┐
│  FastAPI    │
│   /api/     │
└──────┬──────┘
       │
       │ Results
       ↓
┌─────────────┐
│     n8n     │
│  (Slack/    │
│  Dashboard) │
└─────────────┘
```

---

##  Mental Model

> **This is not "an AI".**  
> **This is a data → reasoning → decision → production pipeline.**

**Key Principles:**
- Deterministic over magical
- Testable over black-box
- Observable over opaque
- Human-controlled over autonomous
- Incremental over revolutionary

---

##  Future Enhancements (Post-MVP)

1. **Auto-execution:** Approved actions automatically executed via APIs
2. **Multi-channel:** Google Ads, LinkedIn, TikTok integrations
3. **Memory System:** Learn from past successes/failures
4. **Experiment Engine:** A/B test management and analysis
5. **Predictive Analytics:** Forecast performance trends
6. **Advanced RAG:** Competitor analysis, market trends
7. **Real-time Monitoring:** Alert on performance anomalies
8. **Budget Optimization:** Automatic budget reallocation

---

##  Next Steps

1. Choose Python (recommended) or Node.js
2. Choose first channel: Meta Ads or Google Ads
3. Choose client type: B2B or D2C (affects brand guidelines)
4. Set up development environment
5. Begin Phase 1 implementation

---


