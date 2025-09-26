# API Contracts (T048)

This directory will contain frozen contract snapshots and per-endpoint markdown.

## Planned Structure
- `openapi.json` (generated from FastAPI app) committed for each tagged release.
- `endpoints/` directory with one file per logical endpoint group (auth, user, admin, payout).

## Generation
Example generation script (pseudo):
```
python - <<'PY'
from fastapi.testclient import TestClient
from src.api.app import create_app
import json, pathlib
app = create_app()
client = TestClient(app)
openapi = app.openapi()
pathlib.Path('docs/contracts').mkdir(exist_ok=True, parents=True)
open('docs/contracts/openapi.json','w').write(json.dumps(openapi, indent=2))
PY
```

## Versioning
- Use semantic tagging (e.g., `v0.1.0-contract1`).
- Breaking changes require increment + changelog entry.

## Testing
Contract tests assert status codes and response schema subsets (see `tests/contract/`).
