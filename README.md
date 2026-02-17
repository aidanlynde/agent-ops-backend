# Agent Ops Backend

A specialized backend service for **research and analysis workflows** using Anthropic Claude AI. Completely isolated from production systems with secure file access to ai_sandbox directories.

## Features

- **Claude AI Integration** for research, planning, and analysis
- **Research Brief Generation** with structured findings and decisions  
- **Implementation Planning** (prompt packs) for development tasks
- **Weekly Business Analysis** (pilot memos) with KPI tracking
- **Secure File Access** to ai_sandbox directories only
- **API Key Authentication** for all endpoints
- **Anti-Noise Output Rules** (max 5 findings, 3 decisions, 5 actions)

## Security & Isolation

- ✅ **No production system access**
- ✅ **Read-only file access** limited to ai_sandbox/ directories  
- ✅ **Path traversal protection** and 2MB file size limits
- ✅ **API key authentication** required for all operations
- ✅ **Sanitized error messages** - no secret exposure
- ✅ **Request logging** for audit trails

## Job Types

### 1. prompt_pack
**Development planning and implementation guides**

**Parameters:**
- `feature_name` (required): Name of feature to implement
- `feature_description` (required): Detailed description of requirements  
- `repo_snapshot_key` (optional): Repository snapshot filename from ai_sandbox/repo_snapshots/
- `notes` (optional): Additional context or requirements

**Output:** Structured implementation plan following ai_sandbox/templates/prompt_pack.md

### 2. weekly_pilot_memo
**Business performance analysis and strategic planning**

**Parameters:**
- `pilot_name` (required): Name of business pilot/project
- `week_start_date` (optional): Week start date (YYYY-MM-DD format)
- `data_export_key` (optional): Data export filename from ai_sandbox/pilot_data_exports/
- `notes` (optional): Additional context about the week

**Output:** Weekly analysis following ai_sandbox/templates/weekly_pilot_memo.md

### 3. research_brief
**In-depth research analysis and findings**

**Parameters:**
- `topic` (required): Research topic or area of focus
- `questions` (required): Research questions (array or newline-separated string)
- `context_notes` (optional): Background context and constraints
- `repo_snapshot_key` (optional): Code repository snapshot for analysis
- `data_export_key` (optional): Data export for quantitative analysis

**Output:** Research analysis following ai_sandbox/templates/research_brief.md

### ~~4. lead_list~~ (DEPRECATED)
Lead scraping functionality has been removed. Returns deprecation notice.

## Quick Start

### 1. Environment Setup
```bash
cd agent_ops_backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Anthropic API key
```

### 2. Required Environment Variables
```bash
AGENT_OPS_API_KEY=your_service_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key  # REQUIRED
ANTHROPIC_MODEL=claude-3-5-sonnet-latest
LLM_MAX_OUTPUT_CHARS=9000
```

### 3. Run Service
```bash
python main.py
# OR
uvicorn main:app --reload --port 8080
```

### 4. Test Endpoints
```bash
# Health check
curl http://localhost:8080/health

# API documentation  
open http://localhost:8080/docs
```

## API Reference

### Authentication
All endpoints except `/health` require:
```
Authorization: Bearer YOUR_AGENT_OPS_API_KEY
```

### Core Endpoints

#### Create Research Job
```bash
POST /jobs
Content-Type: application/json
Authorization: Bearer YOUR_AGENT_OPS_API_KEY

# Prompt Pack Example
{
  "type": "prompt_pack",
  "params": {
    "feature_name": "User Authentication System",
    "feature_description": "Implement JWT-based auth with email/password login",
    "repo_snapshot_key": "auth_codebase_v1.zip",
    "notes": "Must integrate with existing user database"
  }
}

# Research Brief Example  
{
  "type": "research_brief",
  "params": {
    "topic": "Mobile App Performance Issues",
    "questions": ["What causes slow startup times?", "Which features have highest crash rates?"],
    "context_notes": "iOS app seeing 15% crash rate in production",
    "data_export_key": "crash_logs_jan_2026.csv"
  }
}

# Weekly Pilot Memo Example
{
  "type": "weekly_pilot_memo", 
  "params": {
    "pilot_name": "E-commerce Checkout Optimization",
    "week_start_date": "2026-02-10",
    "data_export_key": "checkout_metrics_week_6.csv",
    "notes": "Implemented new payment flow on Tuesday"
  }
}
```

#### Job Management
```bash
# List all jobs
GET /jobs

# Get specific job
GET /jobs/{job_id}

# Get job output
GET /jobs/{job_id}/output

# Get latest output by type
GET /outputs/latest?type=research_brief
```

## File Access Patterns

### Supported File References
All file references are optional and safe-loaded from ai_sandbox/:

- `repo_snapshot_key` → `ai_sandbox/repo_snapshots/{filename}`
- `data_export_key` → `ai_sandbox/pilot_data_exports/{filename}`  
- `notes_key` → `ai_sandbox/outputs/{filename}`

### File Security
- ✅ **Path traversal protection** - no "../" or "/" allowed in keys
- ✅ **Size limits** - maximum 2MB per file
- ✅ **Text files only** - UTF-8 encoding required
- ✅ **Graceful failures** - missing files don't break jobs

## Output Format Standards

All outputs follow **anti-noise rules**:

### Structure Requirements
1. **Goal** - Single sentence objective
2. **Inputs Used** - Explicit list of all sources
3. **Template sections** - Follow ai_sandbox/templates structure

### Content Limits
- **Max 5 key findings** per analysis
- **Max 3 critical decisions** requiring action
- **Max 5 next actions** total across all timeframes
- **Specific and actionable** items only

## Example Requests

### Research Brief
```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-key-12345" \
  -d '{
    "type": "research_brief",
    "params": {
      "topic": "API Performance Bottlenecks", 
      "questions": ["What endpoints are slowest?", "What causes database timeouts?"],
      "repo_snapshot_key": "backend_profiling.txt",
      "context_notes": "P95 response times increased 200% this month"
    }
  }'
```

### Prompt Pack
```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-key-12345" \
  -d '{
    "type": "prompt_pack",
    "params": {
      "feature_name": "Real-time Notifications",
      "feature_description": "WebSocket-based notification system for user alerts",
      "notes": "Must work with existing React frontend and Node.js backend"
    }
  }'
```

### Weekly Pilot Memo
```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-key-12345" \
  -d '{
    "type": "weekly_pilot_memo",
    "params": {
      "pilot_name": "Mobile App Beta Test",
      "week_start_date": "2026-02-10", 
      "data_export_key": "beta_metrics_week_3.csv",
      "notes": "Push notifications enabled mid-week"
    }
  }'
```

## Railway Deployment

### Environment Variables
```bash
AGENT_OPS_API_KEY=your_secure_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key  
ALLOWED_ORIGINS=https://your-frontend.com
DATABASE_URL=postgresql://...  # Auto-provided by Railway
```

### Start Command
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Development

### Database Schema
- **jobs**: id, type, status, params_json, timestamps, error_text
- **outputs**: id, job_id, type, content_text, content_type, created_at

### Adding File Support
To add new file directory support:
1. Add directory mapping to `services/file_loader.py`
2. Update parameter validation in generators
3. Document new `*_key` parameter pattern

### Error Handling
- **LLM errors** → Job marked failed with sanitized error message
- **File errors** → Job continues with available inputs only  
- **Invalid params** → 422 validation error before job creation

## Monitoring

### Request Logging
All requests logged with: `METHOD /path - STATUS - DURATION`

### Job Status Tracking
- `queued` → Job created, waiting for execution
- `running` → LLM generation in progress  
- `succeeded` → Output generated and stored
- `failed` → Error occurred, check error_text field

---

**Focus:** Research and analysis workflows only  
**AI Model:** Claude 3.5 Sonnet for high-quality analysis  
**Security:** Read-only access to ai_sandbox directories  
**Output:** Structured, actionable insights following anti-noise principles