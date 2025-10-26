# Async Support

## Async Modules

Symphra Modules natively supports async modules without additional configuration:

```python
import asyncio
from symphra_modules.abc import BaseModule, ModuleMetadata

class AsyncModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(name="async_example")

    async def start(self) -> None:
        """Async start"""
        await asyncio.sleep(1)
        print("Async module started")

    async def stop(self) -> None:
        """Async stop"""
        await asyncio.sleep(0.5)
        print("Async module stopped")
```

## Auto Detection

The framework automatically detects whether modules are sync or async:

```python
# Sync module
class SyncModule(BaseModule):
    def start(self) -> None:
        print("Sync start")

# Async module
class AsyncModule(BaseModule):
    async def start(self) -> None:
        await asyncio.sleep(1)
        print("Async start")

# Mixed usage
manager = ModuleManager()
await manager.load_from_directory("./modules")  # Automatically handles sync and async modules
```

## Async Lifecycle

All lifecycle hooks support async:

```python
class DatabaseModule(BaseModule):
    async def bootstrap(self) -> None:
        """Async initialization"""
        self.pool = await create_connection_pool()

    async def install(self, config: dict | None = None) -> None:
        """Async install"""
        await super().install(config)
        await self.pool.execute("CREATE TABLE IF NOT EXISTS users...")

    async def start(self) -> None:
        """Async start"""
        self.server = await start_database_server()

    async def stop(self) -> None:
        """Async stop"""
        await self.server.shutdown()

    async def uninstall(self) -> None:
        """Async uninstall"""
        await self.pool.close()
```

## Async Dependency Resolution

Dependency resolution supports async modules:

```python
# Async dependency validation
await manager.validate_async_dependencies()

# Async dependency resolution
await manager.resolve_async_dependencies()
```

## Async Event Handling

The event system fully supports async processing:

```python
from symphra_modules.events import EventBus

bus = EventBus()

@bus.subscribe("async.event")
async def async_handler(data: dict):
    """Async event handler"""
    await process_data_async(data)
    await bus.publish("processing.complete", data_id=data["id"])
```

## Concurrency Control

### Async Batch Operations

```python
# Start all modules concurrently
await manager.start_all_concurrent()

# Limit concurrency
await manager.start_all_concurrent(max_concurrency=5)
```

### Async Iteration

```python
# Async iteration over modules
async for module in manager.get_modules_async():
    await module.perform_async_operation()
```

## Async Context Managers

Modules can implement async context managers:

```python
class ResourceModule(BaseModule):
    async def __aenter__(self):
        """Async enter context"""
        self.resource = await acquire_resource()
        return self.resource

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit context"""
        await release_resource(self.resource)
```

## Async Utility Functions

The framework provides async utility functions:

```python
from symphra_modules.utils import async_timeout, async_retry

class NetworkModule(BaseModule):
    @async_timeout(30)  # 30 second timeout
    async def fetch_data(self, url: str) -> dict:
        """Async network request with timeout"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

    @async_retry(max_attempts=3, delay=1.0)  # Retry 3 times, 1 second delay
    async def unreliable_operation(self) -> None:
        """Unreliable operation with retry"""
        if random.random() < 0.7:  # 70% failure rate
            raise ConnectionError("Network error")
        print("Operation succeeded")
```

## Async Testing

Writing tests for async modules:

```python
import pytest
from symphra_modules.testing import AsyncModuleTestCase

class TestAsyncModule(AsyncModuleTestCase):
    async def test_async_start(self):
        """Test async start"""
        module = AsyncModule()
        await module.start()
        self.assertTrue(module.is_started)

    async def test_async_event_handling(self):
        """Test async event handling"""
        bus = EventBus()
        events_processed = []

        @bus.subscribe("test.async")
        async def handler(data):
            await asyncio.sleep(0.1)  # Simulate async processing
            events_processed.append(data)

        await bus.publish("test.async", value=42)

        # Wait for event processing to complete
        await asyncio.sleep(0.2)
        self.assertEqual(len(events_processed), 1)
        self.assertEqual(events_processed[0]["value"], 42)
```

## Performance Considerations

### Async vs Sync

```python
# Sync processing (blocking)
def sync_process_modules(modules):
    for module in modules:
        module.process()  # Process each module sequentially

# Async processing (concurrent)
async def async_process_modules(modules):
    tasks = [module.process_async() for module in modules]
    await asyncio.gather(*tasks)  # Process all modules concurrently
```

### Resource Management

```python
class ConnectionPoolModule(BaseModule):
    async def start(self) -> None:
        # Create connection pool
        self.pool = await create_pool(min_size=5, max_size=20)

    async def stop(self) -> None:
        # Gracefully close connection pool
        await self.pool.close()

    async def get_connection(self):
        """Get connection (with timeout)"""
        return await asyncio.wait_for(
            self.pool.acquire(),
            timeout=10.0
        )
```

## Best Practices

### Avoid Blocking Operations

```python
# Not recommended: blocking operations in async methods
async def bad_example(self):
    # Blocking file I/O
    with open("file.txt", "r") as f:
        data = f.read()  # Blocking!
    return data

# Recommended: use async I/O
async def good_example(self):
    # Async file I/O
    async with aiofiles.open("file.txt", "r") as f:
        data = await f.read()
    return data
```

### Error Handling

```python
async def robust_async_operation(self):
    try:
        await asyncio.wait_for(
            self.unreliable_async_call(),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        logger.error("Operation timed out")
        await self.fallback_operation()
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        await self.cleanup()
        raise
```

### Concurrency Limiting

```python
from asyncio import Semaphore

class RateLimitedModule(BaseModule):
    def __init__(self):
        self.semaphore = Semaphore(10)  # Max 10 concurrent requests

    async def rate_limited_request(self, url: str):
        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.text()
```