# Architecture Overview

## Core Principle: Shared State

No agent talks to another directly. All communication flows through the shared project state.

```
Agent A -> [Write to State] -> [Read by Agent B]
```

This prevents:
- Chinese whispers (message degradation)
- Hidden assumptions (everything is explicit)
- Circular dependencies (state is the mediator)

## State Layers

1. **Vector DB** (Pinecone): Semantic search over project history
2. **Structured DB** (PostgreSQL + Redis): Transactional state
3. **Event Log** (Kafka/Redpanda): Audit trail and replay

## Agent Permissions

| Agent | Risk Level | Can Execute Code | Can Deploy | Needs Approval For |
|-------|-----------|------------------|------------|-------------------|
| CEO | HIGH | No | No | Feature kill, OKR changes |
| PM | MEDIUM | No | No | Budget changes |
| Designer | LOW | No | No | — |
| Frontend | MEDIUM | Yes | No | Code execution |
| Backend | HIGH | Yes | No | Code execution, schema changes |
| QA | MEDIUM | Yes | No | — |
| DevOps | CRITICAL | No | Yes | Deploy, infrastructure changes |
| Marketing | LOW | No | No | — |

## Feedback Loop

```
Marketing campaigns -> User analytics -> CEO review -> PM planning -> Product changes -> Marketing
```

This closes the loop and makes it a company, not just a pipeline.
