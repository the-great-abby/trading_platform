# CLAUDE.md

Guidance for AI agents (and humans) working in this repository. Keep this file
lean; link to deeper docs instead of inlining them.

## What this is

Automated algorithmic trading platform: 50+ strategies (stocks + options),
backtesting, paper/live trading via Public.com, risk management, and
AI-assisted analysis. Python 3.11, FastAPI, PostgreSQL/TimescaleDB/Redis,
Kafka + RabbitMQ, deployed to Kubernetes with a hybrid monolith
(`src/`) + ~54 microservices (`services/`) layout.

## ⚠️ Read this first: v1 is frozen-ish, v2 is planned

This codebase (v1) is being replaced by a hybrid Elixir/Python architecture
("v2"). Before proposing structural changes, read:

- `docs/architecture/hybrid-python-elixir-plan.md` — the v2 plan and
  decisions already made (authoritative)
- `PROJECT.md` (if present) — v2 goals: BEAM spine, ephemeral Python, NATS

Decisions already made — do NOT relitigate or undo:

1. **Makefiles are frozen.** Do not refactor, consolidate, or port them to
   `just` now. A justfile ships with v2, covering only surviving targets.
2. **No new microservices.** v2 consolidates ~54 services into ~12 deployable
   units. New functionality goes into existing services or `src/`.
3. **NATS replaces Kafka + RabbitMQ in v2.** Don't deepen coupling to
   Kafka/RabbitMQ in new code; keep messaging behind existing service layers.
4. **Only strategies with passing backtests get ported to v2.** Don't invest
   in strategies that lack one.

Bug fixes, small features, and documentation improvements to v1 are fine.

## Layout (where things live)

| Path | Contents |
|---|---|
| `src/core/` | Trading engine (`trading_engine.py`) — the main loop |
| `src/strategies/` | All strategy implementations (`base_strategy.py` is the interface) |
| `src/backtesting/engine/` | Backtest engines |
| `src/portfolio/`, `src/risk/` | Portfolio + risk management |
| `src/services/` | In-process services (AI, market data, CQRS, queue) |
| `src/data/` | Market data providers (Polygon, yfinance, Public.com) |
| `src/utils/config.py` | Configuration loading — start here for config questions |
| `services/` | ~54 deployable microservices (see topology doc) |
| `config/strategies/*.yaml` | Strategy configs (paper/live/advanced) |
| `tests/` | `unit/`, `integration/`, `contract/`, `live_trading/` |
| `k8s/`, `deploy/` | Kubernetes manifests, deployment configs |
| `makefiles/` | 26 include-files behind the root Makefile (frozen — see above) |
| `docs/architecture/` | Architecture docs, v2 plan, service topology |

Deeper references:
- Service topology and data flows: `docs/architecture/service-topology.md`
- Deployment workflow (compose variants, k8s): `docs/architecture/deployment-workflow.md`

## Commands

Setup:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.env.example .env   # then fill in API keys — see Configuration
```

Tests (always run before committing):
```bash
make test-run                # full suite
make test-unit               # unit only
make test-integration        # integration only
pytest tests/unit/test_foo.py -v            # single file
pytest -m "elliott_wave and not slow" -v    # by marker
```
Pytest markers are defined in `pytest.ini` (`unit`, `integration`, `contract`,
`slow`, `options`, `ensemble`, `elliott_wave`, `ichimoku`, `validation*`, …).
Coverage gate is 90% (`--cov-fail-under=90`) but note it only measures
`src/testing` and `src/validation`.

Lint/format (match existing style):
```bash
black src/ tests/ && isort src/ tests/
flake8 src/ tests/
mypy src/
```

Discovery:
```bash
make help          # top-level target overview
make wizard        # interactive menu of ~65 curated commands
make status        # platform status
```
The full target list (~530) lives across `makefiles/Makefile.*` — grep there
for domain-specific operations (`live-trading-*`, `paper-trading-*`, `db-*`,
`backtest-*`, `port-forward-*`).

Local stack:
```bash
docker compose -f docker-compose.dev.yml up -d   # full dev stack
python backtests/clean_backtest.py               # run a standalone backtest
```

## Configuration

- **Source of truth for env vars:** `.env` at repo root, created from
  `config.env.example` (most complete template; `.env.template` and
  `.envrc.example` are older variants).
- Strategy behavior: `config/strategies/*.yaml` — separate files for paper,
  live, advanced. Edit the *paper* config unless explicitly working on live.
- Loaded by `src/utils/config.py` and `src/utils/trading_config.py`.
- Kubernetes: ConfigMaps/Secrets under `k8s/`; secret rotation via
  `scripts/update-secrets.sh`.

## Guardrails for AI-driven changes

1. **Never run `live-trading-*` targets or scripts.** They place real-money
   orders through Public.com. Use `paper-trading-*` equivalents. If a task
   seems to require touching live trading execution or
   `config/strategies/live_trading_strategies.yaml`, stop and ask.
2. **Never commit secrets.** API keys live in `.env` (gitignored) and k8s
   Secrets only. If you find a hardcoded credential, flag it — don't copy it.
3. **Risk code is load-bearing.** Changes under `src/risk/` need tests and
   explicit human review; a silent risk-check regression is the worst
   failure mode this repo has.
4. **Don't "clean up" broadly.** Much of v1 is scheduled for deletion in v2;
   large refactors are wasted work. Fix what the task needs.
5. **Strategy changes must keep backtest parity.** The same strategy class
   runs in backtest and live modes — don't fork behavior on mode.
6. **Docs:** new architecture docs go in `docs/architecture/`; status
   reports and one-off analyses go in `docs/history/`, not the repo root.
7. **Commits/PRs:** small, scoped commits; run `make test-run` first; PRs
   are created by humans (agent sessions lack GitHub API access — push the
   branch and provide the compare URL).

## Known gotchas (verified 2026-07-05)

- **Two topologies exist and don't match.** The docker-compose files define
  a ~9-service CQRS stack; Kubernetes deploys ~54 different services. The
  compose `trading-service` etc. are lightweight stubs, NOT the k8s
  services with similar names. Details: `docs/architecture/service-topology.md`.
- **Kafka and EventStore are effectively unused** by `services/*` code —
  they exist only in the compose CQRS world. The real transports are HTTP
  and RabbitMQ. Don't build on Kafka/EventStore.
- `requirements.txt` at the root is a **symlink** to
  `config/requirements/requirements.txt`.
- `scripts/update-secrets.sh` defaults to namespace `default`; the platform
  runs in `trading-system` — always pass `--namespace trading-system`.
- `scripts/deploy-consolidated.sh` and parts of `k8s/README.md` reference
  directories that don't exist (`k8s/infrastructure/`, `k8s/jobs/`) — the
  documented consolidated deploy path is stale.
- Some services listen on different ports than their Dockerfile `EXPOSE`
  claims — trust `uvicorn.run(...)` in the code (see topology doc).

## Testing conventions

- Async tests: `asyncio_mode = auto` — write plain `async def test_*`.
- Fixtures live in `tests/conftest.py` (database, market data mocks,
  portfolio/strategy fixtures) — check there before writing new mocks.
- Integration tests assume the dev stack (`docker-compose.dev.yml`) is up.
- Live-trading tests under `tests/live_trading/` are excluded from normal
  runs — do not wire them into CI or default targets.
