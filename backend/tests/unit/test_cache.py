import asyncio
import json

from redis.exceptions import RedisError

from app.core.cache import CatalogCache, RedisCatalogCache
from app.core.email import Email, RedisEmailQueue
from app.core.events import EventBroker, format_sse
from app.core.idempotency import IdempotencyStore, RedisIdempotencyStore


class FakeRedisKV:
    def __init__(self, *, fail: bool = False):
        self.fail = fail
        self.store: dict[str, str] = {}
        self.lists: dict[str, list[str]] = {}
        self.published: list[tuple[str, str]] = []

    def get(self, key: str) -> str | None:
        if self.fail:
            raise RedisError("redis down")
        return self.store.get(key)

    def setex(self, key: str, _ttl: int, value: str) -> None:
        if self.fail:
            raise RedisError("redis down")
        self.store[key] = value

    def incr(self, key: str) -> int:
        if self.fail:
            raise RedisError("redis down")
        val = int(self.store.get(key, "0")) + 1
        self.store[key] = str(val)
        return val

    def rpush(self, key: str, value: str) -> None:
        if self.fail:
            raise RedisError("redis down")
        self.lists.setdefault(key, []).append(value)

    def lpop(self, key: str) -> str | None:
        if self.fail:
            raise RedisError("redis down")
        items = self.lists.get(key, [])
        return items.pop(0) if items else None

    def blpop(self, key: str, timeout: int = 0) -> tuple[str, str] | None:
        item = self.lpop(key)
        return (key, item) if item is not None else None

    def llen(self, key: str) -> int:
        if self.fail:
            raise RedisError("redis down")
        return len(self.lists.get(key, []))

    def publish(self, channel: str, payload: str) -> int:
        if self.fail:
            raise RedisError("redis down")
        self.published.append((channel, payload))
        return 1


class TestCatalogCache:
    def test_in_memory_cache_hit_miss_and_invalidation(self):
        cache = CatalogCache(enabled=True, ttl_seconds=60)
        assert cache.get("categories") is None
        assert cache.misses == 1

        cache.set("categories", [{"id": 1, "slug": "starters"}])
        assert cache.get("categories") == [{"id": 1, "slug": "starters"}]
        assert cache.hits == 1

        new_ver = cache.invalidate()
        assert new_ver == 2
        assert cache.get("categories") is None

    def test_redis_catalog_cache_versioned_invalidation(self):
        fake = FakeRedisKV()
        cache = RedisCatalogCache(fake, prefix="test")

        assert cache.get("products:1") is None
        cache.set("products:1", {"total": 10})
        assert cache.get("products:1") == {"total": 10}
        assert cache.stats() == {"hits": 1, "misses": 1, "version": 0}

        cache.invalidate()
        assert cache.get("products:1") is None
        assert cache.stats()["version"] == 1

    def test_redis_catalog_cache_degrades_gracefully(self):
        cache = RedisCatalogCache(FakeRedisKV(fail=True), prefix="test")
        assert cache.get("k") is None
        cache.set("k", {"ok": True})
        assert cache.invalidate() >= 2


class TestIdempotencyStore:
    def test_in_memory_idempotency(self):
        store = IdempotencyStore(ttl_seconds=60)
        assert store.get("order:1", "key-abc") is None
        store.set("order:1", "key-abc", {"id": 42})
        assert store.get("order:1", "key-abc") == {"id": 42}
        assert store.get("order:2", "key-abc") is None

    def test_redis_idempotency_and_fallback(self):
        fake = FakeRedisKV()
        store = RedisIdempotencyStore(fake, prefix="test")
        store.set("order:1", "k1", {"id": 7})
        assert store.get("order:1", "k1") == {"id": 7}

        fake.fail = True
        assert store.get("order:1", "k1") == {"id": 7}


class TestEventBrokerAndWorkerQueue:
    def test_event_broker_publishes_and_streams_once(self):
        fake = FakeRedisKV()
        broker = EventBroker(fake, prefix="test")
        broker.publish("order:99", {"id": 99, "status": "CONFIRMED"})
        assert broker.latest("order:99") == {"id": 99, "status": "CONFIRMED"}

        async def collect():
            return [
                frame
                async for frame in broker.stream(
                    "order:99", {"id": 99, "status": "PENDING"}, once=True
                )
            ]

        frames = asyncio.run(collect())
        assert len(frames) == 2
        assert frames[0] == format_sse("snapshot", {"id": 99, "status": "PENDING"})
        assert frames[1] == format_sse("update", {"id": 99, "status": "CONFIRMED"})

    def test_worker_enqueue_only_and_consume_one(self):
        fake = FakeRedisKV()
        delivered: list[Email] = []

        class Recorder:
            def send(self, email: Email) -> None:
                delivered.append(email)

        producer = RedisEmailQueue(fake, Recorder(), prefix="test", enqueue_only=True)
        consumer = RedisEmailQueue(fake, Recorder(), prefix="test", enqueue_only=False)

        producer.send(Email(to="u@example.com", subject="Hi", text="Hello"))
        assert len(delivered) == 0
        assert producer.queue_stats() == {"queued": 1, "dead_letter": 0}

        assert consumer.consume_one(timeout=1) is True
        assert len(delivered) == 1
        assert json.loads(json.dumps(delivered[0].to)) == "u@example.com"
        assert consumer.queue_stats() == {"queued": 0, "dead_letter": 0}
