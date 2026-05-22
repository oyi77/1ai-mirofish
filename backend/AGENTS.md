<!-- Generated: 2026-05-06 -->

# MiroFish Backend - Flask API Server

## Purpose
Python Flask backend providing REST API for the MiroFish prediction engine. Orchestrates multi-agent simulations, manages knowledge graphs, and generates AI-powered reports using LLM and Zep integration.

**Tech**: Python 3.11+, Flask 3.0+, CAMEL OASIS, Zep Cloud, OpenAI SDK

## Quick Start

```bash
# Setup
uv install                    # or: pip install -r requirements.txt

# Run
python run.py                 # Starts Flask on 0.0.0.0:5001

# Test
pytest
```

## Directory Structure

```
backend/
├── app/
│   ├── api/                  # REST API routes
│   │   ├── graph.py         # Graph building endpoints
│   │   ├── report.py        # Report generation endpoints
│   │   ├── simulation.py     # Simulation execution endpoints
│   │   └── __init__.py       # Blueprint registration
│   │
│   ├── services/             # Core business logic
│   │   ├── graph_builder.py                 # Knowledge graph construction
│   │   ├── ontology_generator.py            # Entity/relationship extraction
│   │   ├── oasis_profile_generator.py       # Agent personality generation
│   │   ├── report_agent.py                  # Report generation
│   │   ├── simulation_config_generator.py   # Simulation configuration
│   │   ├── simulation_runner.py             # OASIS execution
│   │   ├── simulation_manager.py            # Multi-simulation coordination
│   │   ├── simulation_ipc.py                # Inter-process communication
│   │   ├── zep_entity_reader.py             # Zep graph reading
│   │   ├── zep_graph_memory_updater.py      # Zep memory updates
│   │   ├── zep_tools.py                     # Zep API utilities
│   │   ├── text_processor.py                # Text chunking/processing
│   │   └── __init__.py
│   │
│   ├── models/               # Data models
│   │   ├── project.py        # Project lifecycle (CREATED → COMPLETED)
│   │   ├── task.py           # Task tracking
│   │   └── __init__.py
│   │
│   ├── utils/                # Utilities
│   │   ├── file_parser.py    # PDF/MD/TXT parsing
│   │   ├── llm_client.py     # LLM API wrapper
│   │   ├── locale.py         # i18n translation
│   │   ├── logger.py         # Structured logging
│   │   ├── polymarket_client.py  # Prediction market API
│   │   ├── retry.py          # Exponential backoff
│   │   ├── zep_paging.py     # Zep pagination
│   │   └── __init__.py
│   │
│   ├── __init__.py           # Flask app factory
│   └── config.py             # Centralized configuration
│
├── scripts/                  # Batch utilities
│   ├── run_parallel_simulation.py
│   ├── run_twitter_simulation.py
│   ├── run_reddit_simulation.py
│   ├── action_logger.py
│   └── test_profile_format.py
│
├── logs/                     # Runtime logs
├── uploads/                  # User-uploaded files (PDFs, TXT, MD)
│
├── run.py                    # Entry point (main)
├── pyproject.toml           # Project config (uv)
├── requirements.txt         # Pip dependencies
└── uv.lock                  # uv lock file
```

## API Routes

### Graph Management (`/api/graph`)
```
POST   /project/upload           - Create project from uploaded file
GET    /project/<id>             - Get project details
GET    /project/list             - List all projects
POST   /project/<id>/delete      - Delete project

POST   /ontology/generate        - Generate ontology from documents
POST   /build                    - Build knowledge graph
GET    /<id>/status              - Check graph build status
```

### Simulations (`/api/simulation`)
```
POST   /create                   - Create simulation config
POST   /run                      - Execute simulation
GET    /<id>/status              - Get simulation status
GET    /<id>/results             - Get simulation results
POST   /<id>/cancel              - Cancel running simulation
```

### Reports (`/api/report`)
```
POST   /generate                 - Generate report from simulation
GET    /<id>                     - Get report details
GET    /list                     - List all reports
```

## Core Services

### Graph Pipeline
1. **FileParser** (`utils/file_parser.py`) - Parse PDF/MD/TXT with encoding detection
2. **TextProcessor** (`services/text_processor.py`) - Chunk text with overlap
3. **OntologyGenerator** (`services/ontology_generator.py`) - Extract entities and relationships
4. **GraphBuilder** (`services/graph_builder.py`) - Build knowledge graph
5. **ZepGraphMemoryUpdater** (`services/zep_graph_memory_updater.py`) - Persist to Zep

### Simulation Pipeline
1. **SimulationConfigGenerator** - Create OASIS agent configuration
2. **OASISProfileGenerator** - Generate agent personalities/behaviors
3. **SimulationRunner** - Execute simulation in subprocess
4. **SimulationIPC** - Communicate with subprocess
5. **SimulationManager** - Coordinate multiple simulations

### Report Generation
- **ReportAgent** (`services/report_agent.py`) - LLM-powered analysis and insights

## Configuration (from `.env`)

```bash
# LLM (OpenAI-compatible)
LLM_API_KEY=your_key
LLM_BASE_URL=https://api.openai.com/v1  # or Aliyun, local, etc.
LLM_MODEL_NAME=gpt-4o-mini              # or qwen-plus

# Memory Graph
ZEP_API_KEY=your_zep_key

# Prediction Markets
POLYMARKET_GAMMA_URL=https://gamma-api.polymarket.com
POLYMARKET_DATA_URL=https://data-api.polymarket.com
POLYMARKET_CLOB_URL=https://clob.polymarket.com

# Server
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5001

# Simulation
OASIS_DEFAULT_MAX_ROUNDS=10

# File Upload
MAX_CONTENT_LENGTH=52428800  # 50MB
UPLOAD_FOLDER=./uploads
ALLOWED_EXTENSIONS=pdf,md,txt,markdown

# Text Processing
DEFAULT_CHUNK_SIZE=500
DEFAULT_CHUNK_OVERLAP=50
```

## Key Patterns

### 1. Project Context Persistence
Projects store multi-step state server-side to avoid passing large data structures:
```python
# models/project.py
class Project:
    status: ProjectStatus  # CREATED → ONTOLOGY_GENERATED → GRAPH_BUILDING → COMPLETED
    ontology: Dict        # Generated ontology
    graph_id: str         # Zep graph reference
    files: List[Dict]     # Uploaded files metadata
```

### 2. Task Lifecycle
Long-running operations tracked with enum status:
```python
class TaskStatus(Enum):
    PENDING, RUNNING, COMPLETED, FAILED
```

### 3. Process Isolation
OASIS simulations run in isolated subprocess with IPC:
```python
# services/simulation_ipc.py
class SimulationIPCClient:
    def send_command(cmd: CommandType) -> IPCResponse
    def get_agent_actions() -> List[AgentAction]
```

### 4. Configuration as Code
All configuration from `.env` with defaults:
```python
# config.py
class Config:
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
```

### 5. Error Handling & Retries
Exponential backoff for transient failures:
```python
# utils/retry.py
@retry_with_backoff(max_retries=3)
def call_external_api():
    ...
```

## Adding Features

### Add a New API Endpoint

1. Create handler in `app/api/graph.py` (or appropriate file):
```python
@graph_bp.route('/new-endpoint', methods=['POST'])
def new_endpoint():
    data = request.get_json()
    # Your logic
    return jsonify({"success": True, "data": result})
```

2. Blueprint automatically registered in `app/__init__.py`

### Add a Service

1. Create `app/services/my_service.py`:
```python
class MyService:
    def process(self, data):
        # Implementation
        pass
```

2. Import in API handler:
```python
from ..services.my_service import MyService
service = MyService()
```

### Modify Simulation Config

Edit `services/simulation_config_generator.py` to change:
- Agent personality traits
- Round count defaults
- Environment parameters

## Testing

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_graph_builder.py

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_graph_builder.py::test_entity_extraction
```

## Dependencies

### Core
- `flask>=3.0.0` - Web framework
- `flask-cors>=6.0.0` - CORS support
- `openai>=1.0.0` - LLM API client
- `zep-cloud==3.13.0` - Graph memory
- `camel-oasis==0.2.5` - Multi-agent framework
- `camel-ai==0.2.78` - CAMEL core

### File Processing
- `PyMuPDF>=1.24.0` - PDF parsing
- `chardet>=5.0.0` - Encoding detection
- `charset-normalizer>=3.0.0` - Text normalization

### Utilities
- `python-dotenv>=1.0.0` - .env loading
- `pydantic>=2.0.0` - Data validation

### Dev
- `pytest>=8.0.0` - Testing
- `pytest-asyncio>=0.23.0` - Async test support

## Performance Considerations

- **Graph Building**: Time scales with document size; text chunking configurable
- **Simulations**: Linear with round count; ~1-2 LLM calls per agent per round
- **Memory**: Each agent stores state in Zep; monitor usage with large graphs
- **File Upload**: Max 50MB (configurable)
- **Parallel**: Use `scripts/run_parallel_simulation.py` for batch runs

## Debugging

```bash
# Enable debug logging
FLASK_DEBUG=True python run.py

# Check logs
tail -f logs/mirofish.log

# Inspect uploaded files
ls -la uploads/

# Check Zep integration
# Query Zep Cloud console at https://app.getzep.com/
```

## Known Issues

1. **Subprocess Cleanup**: Windows may require explicit process termination
2. **File Encoding**: Non-UTF8 files auto-detected; some edge cases possible
3. **Rate Limits**: Large simulations (40+ rounds) may exceed LLM API limits
4. **Zep Quota**: Free tier adequate for development; prod requires paid plan

## Architecture Diagram

```
User Upload
    ↓
FileParser → TextProcessor
    ↓
OntologyGenerator (LLM)
    ↓
GraphBuilder → Zep Cloud (persist)
    ↓
SimulationConfigGenerator
    ↓
OASISProfileGenerator (LLM)
    ↓
SimulationRunner (subprocess)
    ├→ Agent 1, Agent 2, ... (parallel)
    ├→ IPC Communication
    └→ Zep Memory Updates
    ↓
ReportAgent (LLM)
    ↓
JSON Report → Frontend
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "LLM_API_KEY not found" | Check `.env` file exists in project root |
| "Zep connection failed" | Verify `ZEP_API_KEY` and internet connection |
| "Subprocess timeout" | Increase `OASIS_DEFAULT_MAX_ROUNDS` gradually; 40+ rounds uses lots of API |
| "File upload fails" | Check file extension in ALLOWED_EXTENSIONS; max size 50MB |
| "Port 5001 already in use" | Change FLASK_PORT in .env or `sudo lsof -i :5001; kill -9 <PID>` |

