"""Production observability: Prometheus metrics exporter (`/api/metrics`) and deep readiness
probe (`/api/health/ready`) inspecting PostgreSQL, Redis, SQLAlchemy QueuePool, CatalogCache
and RedisEmailQueue.
"""

import threading
import time
from collections import Counter
from typing import Any

from fastapi import FastAPI
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import engine

BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5)


class MetricsRegistry:
    """Thread-safe in-process HTTP metrics collector."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.requests_total: Counter[tuple[str, str]] = Counter()
        self.status_class_total: Counter[str] = Counter()
        self.rate_limited_total = 0
        self.duration_count = 0
        self.duration_sum = 0.0
        self.duration_buckets: Counter[float] = Counter()

    def record(self, method: str, path: str, status: int, duration_seconds: float) -> None:
        status_class = f"{status // 100}xx"
        with self._lock:
            self.requests_total[(method, status_class)] += 1
            self.status_class_total[status_class] += 1
            if status == 429:
                self.rate_limited_total += 1
            self.duration_count += 1
            self.duration_sum += duration_seconds
            for b in BUCKETS:
                if duration_seconds <= b:
                    self.duration_buckets[b] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "requests_total": dict(self.requests_total),
                "status_class_total": dict(self.status_class_total),
                "rate_limited_total": self.rate_limited_total,
                "duration_count": self.duration_count,
                "duration_sum": round(self.duration_sum, 6),
                "duration_buckets": {str(b): self.duration_buckets[b] for b in BUCKETS},
            }


metrics_registry = MetricsRegistry()


def _pool_stat(pool: Any, name: str) -> int:
    attr = getattr(pool, name, 0)
    return int(attr() if callable(attr) else (attr or 0))


def pool_metrics() -> dict[str, int]:
    pool = engine.pool
    return {
        "size": _pool_stat(pool, "size"),
        "checked_in": _pool_stat(pool, "checkedin"),
        "checked_out": _pool_stat(pool, "checkedout"),
        "overflow": _pool_stat(pool, "overflow"),
    }


def check_readiness(app: FastAPI, db: Session) -> dict[str, Any]:
    settings = get_settings()

    # 1. Database probe
    db_start = time.perf_counter()
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    db_latency_ms = round((time.perf_counter() - db_start) * 1000, 2)

    # 2. Redis probe & email queue depth
    redis_ok = True
    redis_latency_ms = 0.0
    email_queue = {"queued": 0, "dead_letter": 0}
    if settings.redis_configured:
        r_start = time.perf_counter()
        try:
            client = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            client.ping()
            prefix = settings.redis_key_prefix
            email_queue = {
                "queued": int(client.llen(f"{prefix}:email:queue")),
                "dead_letter": int(client.llen(f"{prefix}:email:dead")),
            }
        except RedisError:
            redis_ok = False
        redis_latency_ms = round((time.perf_counter() - r_start) * 1000, 2)

    # 3. Catalog cache stats
    cache = getattr(app.state, "catalog_cache", None)
    if cache is not None and hasattr(cache, "stats"):
        cache_stats = cache.stats()
    elif cache is not None:
        cache_stats = {
            "hits": cache.hits,
            "misses": cache.misses,
            "version": getattr(cache, "_version", 1),
        }
    else:
        cache_stats = {"hits": 0, "misses": 0, "version": 1}

    overall = "ok" if (db_ok and redis_ok) else "degraded"
    return {
        "status": overall,
        "database": {
            "status": "ok" if db_ok else "down",
            "latency_ms": db_latency_ms,
            "pool": pool_metrics(),
        },
        "redis": {
            "configured": settings.redis_configured,
            "status": "ok" if redis_ok else "down",
            "latency_ms": redis_latency_ms,
        },
        "email_queue": email_queue,
        "catalog_cache": cache_stats,
    }


def render_prometheus(app: FastAPI, db: Session) -> str:
    readiness = check_readiness(app, db)
    snap = metrics_registry.snapshot()
    pool = readiness["database"]["pool"]
    cache = readiness["catalog_cache"]
    eq = readiness["email_queue"]

    lines = [
        "# HELP dateno_up 1 if the service and its backing stores are healthy.",
        "# TYPE dateno_up gauge",
        f"dateno_up {1 if readiness['status'] == 'ok' else 0}",
        "# HELP dateno_db_latency_ms Database ping latency in milliseconds.",
        "# TYPE dateno_db_latency_ms gauge",
        f"dateno_db_latency_ms {readiness['database']['latency_ms']}",
        "# HELP dateno_db_pool_connections SQLAlchemy connection pool state.",
        "# TYPE dateno_db_pool_connections gauge",
        f'dateno_db_pool_connections{{state="size"}} {pool["size"]}',
        f'dateno_db_pool_connections{{state="checked_in"}} {pool["checked_in"]}',
        f'dateno_db_pool_connections{{state="checked_out"}} {pool["checked_out"]}',
        f'dateno_db_pool_connections{{state="overflow"}} {pool["overflow"]}',
        "# HELP dateno_catalog_cache_operations_total Catalog read-through cache hits and misses.",
        "# TYPE dateno_catalog_cache_operations_total counter",
        f'dateno_catalog_cache_operations_total{{result="hit"}} {cache["hits"]}',
        f'dateno_catalog_cache_operations_total{{result="miss"}} {cache["misses"]}',
        "# HELP dateno_email_queue_depth Outbound email queue and dead-letter lengths.",
        "# TYPE dateno_email_queue_depth gauge",
        f'dateno_email_queue_depth{{queue="pending"}} {eq["queued"]}',
        f'dateno_email_queue_depth{{queue="dead_letter"}} {eq["dead_letter"]}',
        "# HELP dateno_http_requests_total Total HTTP requests by method and status class.",
        "# TYPE dateno_http_requests_total counter",
    ]
    for (method, status_class), count in sorted(snap["requests_total"].items()):
        lines.append(
            f'dateno_http_requests_total{{method="{method}",status="{status_class}"}} {count}'
        )
    lines.extend(
        [
            "# HELP dateno_rate_limited_requests_total Total HTTP 429 rate-limited responses.",
            "# TYPE dateno_rate_limited_requests_total counter",
            f"dateno_rate_limited_requests_total {snap['rate_limited_total']}",
            "# HELP dateno_http_request_duration_seconds HTTP request latency histogram.",
            "# TYPE dateno_http_request_duration_seconds histogram",
        ]
    )
    for b in BUCKETS:
        lines.append(
            f'dateno_http_request_duration_seconds_bucket{{le="{b}"}} '
            f"{snap['duration_buckets'][str(b)]}"
        )
    lines.append(
        f'dateno_http_request_duration_seconds_bucket{{le="+Inf"}} {snap["duration_count"]}'
    )
    lines.append(f"dateno_http_request_duration_seconds_sum {snap['duration_sum']}")
    lines.append(f"dateno_http_request_duration_seconds_count {snap['duration_count']}")
    return "\n".join(lines) + "\n"
