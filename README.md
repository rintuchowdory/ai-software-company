# 🤖 AI Software Company

A fully autonomous AI-native software company. 8 specialized agents work together through a shared state architecture to design, build, test, deploy, and market software.

## Architecture

```
CEO AI → PM AI → Designer AI → Frontend AI + Backend AI → QA AI → DevOps AI → Marketing AI
                                                            ↓
                                                    Feedback Loop → CEO AI
```

**Core Principle:** No agent talks to another directly. All communication flows through the shared project state.

## Quick Start

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd ai-software-company
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start infrastructure
docker-compose up -d

# 4. Run the orchestrator
python -m orchestrator.main --trigger weekly_review
```

## Agents

| Agent | Role | Cost/Run | Tools |
|-------|------|----------|-------|
| CEO | Strategy & OKRs | $0.20 | read_state, write_state, human_approval |
| PM | Roadmap & PRDs | $0.15 | read_state, write_state, message |
| Designer | UI/UX Specs | $0.12 | read_state, write_state |
| Frontend | React/TypeScript | $0.35 | read_state, write_state, execute_code |
| Backend | APIs & DB | $0.35 | read_state, write_state, execute_code |
| QA | Testing & Quality | $0.50 | read_state, write_state, execute_code, run_tests |
| DevOps | Deploy & Infra | $0.25 | read_state, write_state, deploy, terraform |
| Marketing | Growth & Content | $0.15 | read_state, write_state, publish_content |

## Project Structure

```
.
├── agents/              # Agent definitions (prompts, schemas, examples)
├── orchestrator/        # LangGraph workflow engine
├── memory/              # Shared state (vector + structured + events)
├── security/            # Permission system, sanitization, gates
├── frontend/            # Generated frontend code
├── backend/             # Generated backend code
├── infra/               # Terraform, K8s, monitoring
├── tests/               # Integration tests
├── scripts/             # Backup, maintenance
└── docs/                # Documentation
```

## Phased Rollout

- **Week 1-2:** Closed loop (PM + Fullstack + Deploy)
- **Week 3-4:** Add Designer, split Frontend/Backend
- **Month 2:** Add QA, human approval gates
- **Month 3:** Add CEO, Marketing
- **Month 4+:** Add DevOps, scale infrastructure

## Cost

| Scenario | Monthly |
|----------|---------|
| Conservative (3 agents) | ~$800 |
| Full company (8 agents) | ~$2,500 |
| Heavy usage | ~$4,000 |

## License

MIT
