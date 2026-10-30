# Load and abuse tests

Scripts that put the Docker Compose stack under load and attack, to check that it keeps
serving real visitors. They run [k6](https://k6.io) and Python in throwaway containers on
the stack's network, so the attacker has its own address, while `visitor.sh` plays a real
visitor from the host. They only read data or sign in with unknown emails, so they leave the
database as it was.

Run them against a local stack (`docker compose up -d`) from the repository root, never
against a server you do not own.

```bash
# A real visitor's experience while something else runs (seconds)
loadtest/visitor.sh 25

# One endpoint under 50 concurrent clients for 20 s, with peak CPU per container
loadtest/endpoint.sh '/api/products?page=1' 50

# Flood from one address (expect 429s for it, no failures for the visitor)
loadtest/visitor.sh 25 & loadtest/endpoint.sh '/api/products?page=1' 300; wait

# Many addresses, each just under nginx's per-address limit
for i in $(seq 1 10); do
  docker run --rm -d --network restaurant_project_default -v "$PWD/loadtest:/scripts" \
    -e TARGET='/api/products/search?q=bo' grafana/k6 run --quiet /scripts/steady.js
done

# Slowloris: 4000 connections sending headers slowly for 35 s
docker run --rm --network restaurant_project_default -v "$PWD/loadtest:/s" \
  python:3.12-slim python -I /s/slowloris.py web 4000 35
```

To measure raw capacity rather than the limits, start the backend with them off, and
restore it afterwards (`login.js` needs this too, since each address may only try 10
sign-ins a minute):

```bash
docker compose -f docker-compose.yml -f loadtest/no-limits.yml up -d backend
docker run --rm --network restaurant_project_default -v "$PWD/loadtest:/scripts" \
  -e RATE=20 grafana/k6 run --quiet /scripts/login.js
docker compose up -d backend
```

## Results (2026-10-30, 20-core WSL2 machine, one backend process)

| Test | Result |
|---|---|
| Static files (nginx) | ~70,000-110,000 req/s, p95 < 5 ms |
| Menu list / dish / search (backend) | ~130 / 220 / 300 req/s at 50 clients; 1-3 SQL queries, ~9 ms each in Python |
| One address flooding the API, 300 clients | ~72,000 req/s all refused by nginx with 429; real visitor 100% OK |
| 10-20 addresses, 18 req/s each, on search | each capped at 300 req/min by the backend; visitor p95 12 ms, no failures |
| Sign-ins (Argon2, ~50 ms each) | ~0.14 CPU core per sign-in/s; 40/s used 6 cores and ~230 MB; visitors unaffected |
| Slowloris, 4000 connections | all cut after 10 s of silence; visitor p95 6 ms |
| 7 MB body / 100 KB JSON | 413 from nginx; only the photo upload accepts up to 6 MB |
| Known vs unknown email at sign-in | same 42 ms; no way to tell accounts apart |

Issues found and fixed while testing: nginx opened a new connection to the backend per
request, so a single address at a few thousand requests a second exhausted local ports and
every visitor got 502s (now keepalive plus per-address limits in nginx); API bodies of up to
6 MB were parsed (now 64 KB except photo uploads); dish photos went through Python (now
served by nginx); a page number past the integer range returned 500 (now 422, and any
out-of-range value is a 400).

## Limits that remain

- **One backend process.** Around 100-300 API requests a second, depending on the endpoint.
  More processes need the rate-limit counters in a shared store such as Redis first.
- **A large botnet.** Per-address limits stop a few addresses, not thousands; that needs a
  CDN or DDoS protection in front (for example Cloudflare).
- **Shared addresses.** People behind one office or campus address share nginx's 20 req/s
  and the backend's per-address limits.
