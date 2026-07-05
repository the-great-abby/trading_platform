# Deployment Workflow

How the platform actually builds, runs, and deploys — including which
documented paths are broken. Verified against the repo on 2026-07-05.

## Docker Compose variants

| File | Purpose |
|---|---|
| `docker-compose.dev.yml` | **Primary local dev stack.** One root `Dockerfile.dev` image with the repo live-mounted at `/app`; runs 8 internal microservices behind a single exposed api-gateway (host :8000). Includes `trading-cli` (dev shell), `trading-bot-test` (pytest container), and dev + test infra (Postgres, Redis, Kafka, EventStore, RabbitMQ, Prometheus/Grafana). |
| `docker-compose.yml` | The full CQRS reference stack (gateway, command/query APIs, 8 domain services, public-api, write/read DBs, EventStore, Kafka, Redis, InfluxDB, Prometheus/Grafana, full ELK). Heaviest stack; more architecture showcase than daily driver. |
| `docker-compose.test.yml` | Test-only: `timescaledb-test` (:5433), `redis-test` (:6380), `rabbitmq-test`, plus a `test-runner` (from `Dockerfile.test`) that seeds via `scripts/setup_test_database.py` and runs `pytest tests/cqrs/` → `test-results/report.html`. |
| `docker-compose.quick-wins.yml` | Standalone caching/logging demo + `health-dashboard` (:8000) + Redis L2 cache. Reads `.env`. |
| `docker-compose.registry.yml` | Override for `docker-compose.yml` that tags/pushes images to `host.docker.internal:5000/trading-bot-*`. Use as `-f docker-compose.yml -f docker-compose.registry.yml`. Note: this registry differs from the k8s registry (below). |

## Kubernetes deployment

- **Raw manifests only** — no Helm, no kustomize. ~140 flat YAMLs in `k8s/`
  plus `k8s/core/` (namespace), `k8s/services/` (consolidated
  `core-services.yaml`, `dashboard-services.yaml`), `k8s/secrets/`,
  `k8s/templates/`, `k8s/deprecated/`.
- **Namespace:** `trading-system` (canonical). LLM infra lives in
  `ollama-controller`; external DBs in `postgres-infra`.
- **Simplest working path:** `kubectl apply -f k8s/` then
  `make port-forward-all` (or `scripts/robust-port-forward.sh start`).
- **Consolidated manifests:** `k8s/services/core-services.yaml` deploys
  strategy-service, market-data-service, market-data-worker, backtest-api;
  `dashboard-services.yaml` deploys the dashboard set. All use images
  `localhost:32000/<name>:latest`, `/health` liveness + `/ready` readiness,
  `trading-secrets` Secret + `trading-config` ConfigMap.
- Many of the 140 YAMLs are one-off Jobs/CronJobs (40+ `backtest-*.yaml`,
  news/earnings/options scans, position monitor, account/order sync,
  pg-backup).

### ⚠️ Known-broken deploy paths

- `scripts/deploy-consolidated.sh` and `k8s/README.md` reference
  `k8s/infrastructure/` and `k8s/jobs/` — **these directories do not
  exist**. The documented "consolidated deploy" is stale.
- `scripts/build-and-deploy.sh` references `services/kubernetes-rag-chat-rs`
  — the actual directory is `kubernetes-rag-chat`.

## Image build & registry

- **Two divergent registry schemes:**
  - k8s world (primary): `localhost:32000/<service>:latest` — a NodePort
    registry (NodePort 32000 → internal 5000, see `config/registry.env`);
    build scripts reach it via `kubectl port-forward service/registry
    32000:5000`.
  - compose world: `host.docker.internal:5000/trading-bot-<service>:latest`.
- Root Dockerfiles are multi-purpose bases (`Dockerfile.dev`, `.test`,
  `.k8s`, `.optimized`, `.quick-wins`, `.risk-management`, `.validation`,
  `.backtest-script`). ~50 of 54 services also have their own Dockerfile.
- Rebuild + redeploy one service:
  `make -f makefiles/Makefile.services docker-build-<svc>` then
  `k8s-deploy-<svc>` (rollout restart), or combined `update-<svc>` —
  dedicated targets exist for live-trading/strategy/market-data; other
  services are built manually (`cd services/<svc> && docker build …`).

## Dev → test → prod reality

1. **Dev:** `docker compose -f docker-compose.dev.yml up -d` (code
   live-mounted, gateway on :8000) — or the k8s path above for
   cluster-faithful behavior.
2. **Test:** `make test-run` locally; containerized CQRS tests via
   `docker-compose.test.yml`; the dev stack's `trading-bot-test` container
   runs the full suite.
3. **"Prod":** the local k8s cluster (`trading-system` namespace). There is
   **no CI/CD pipeline** — `.github/` has no workflows; no Jenkinsfile.
   Deployment is Make-target- and script-driven, manual. Versioning via
   GitVersion (`makefiles/Makefile.versioning`). Pre-commit hooks exist
   (`.pre-commit-config.yaml`).

## Secrets

- Mechanism: **k8s Secrets** + `trading-config` ConfigMap. Manifest
  templates in `k8s/secrets/` (api-keys, database, live-trading Fernet
  `ENCRYPTION_KEY`) hold placeholders only — never commit real values.
- `scripts/update-secrets.sh` sources `.env` and creates per-key secrets +
  a combined `db-credentials` secret. **Gotcha: its default namespace is
  `default`, not `trading-system`** — pass `--namespace trading-system`.
- Helpers: `makefiles/Makefile.secrets`, `scripts/list-secrets.sh`,
  `scripts/secret-helpers.sh`, `.envrc` (pulls keys back out of the cluster
  via direnv).

## Configuration files (source-of-truth ranking)

1. `.env` (gitignored) — the real runtime config. Created from
   `config.env.example` (per README; broadest template).
2. `.env.template` — k8s/live-trading-flavored variant; `.envrc.example` —
   direnv/port-forward convenience. Both narrower than
   `config.env.example`.
3. `config/*.yaml|json` — strategy and trading behavior (paper/live/
   ensemble configs, LLM providers), read by engines and `scripts/*`, not
   by k8s (which uses ConfigMap/Secret env).
4. `config/registry.env` — registry ports/URLs.

Known conflict: `DATABASE_URL` differs across templates (sqlite vs
timescale vs localhost port-forward) and 15+ distinct Postgres URLs exist
across k8s manifests. The de-facto production DB is
`timescaledb.trading-system.svc.cluster.local:5432/trading_bot`.

## Relation to the v2 plan

v2 (see `hybrid-python-elixir-plan.md`) removes this entire K8s-per-service
model in favor of a native BEAM spine + ephemeral Python jobs on the
existing Rancher Desktop cluster. Treat investments in the current deploy
machinery accordingly — fix breakage that blocks daily work; don't extend
it.
