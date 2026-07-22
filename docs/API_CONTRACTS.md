# API Contract Schema

All API contracts are stored in shared state as OpenAPI 3.0 specs.

## Contract Lifecycle

1. Backend designs API -> writes OpenAPI spec
2. Backend updates `project_state.api_contracts`
3. Backend notifies consumers (Frontend, QA)
4. Frontend implements against contract
5. QA tests against contract
6. Contract changes trigger version bump

## Breaking Changes

A change is breaking if:
- Required field added to request
- Field type changed
- Endpoint removed
- Response structure changed

Breaking changes require:
- Version bump (v2 -> v3)
- Migration guide
- Consumer notification
- Deprecation period (min 2 sprints)

## Example Contract

```json
{
  "endpoint": "v2/checkout",
  "version": "2.1.0",
  "schema": {
    "openapi": "3.0.0",
    "paths": {
      "/checkout": {
        "post": {
          "requestBody": {
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "amount": {"type": "number", "minimum": 0},
                    "currency": {"type": "string", "enum": ["USD", "EUR"]},
                    "idempotencyKey": {"type": "string", "format": "uuid"}
                  },
                  "required": ["amount", "currency", "idempotencyKey"]
                }
              }
            }
          }
        }
      }
    }
  },
  "consumers": ["frontend", "qa", "marketing"],
  "breaking": false
}
```
