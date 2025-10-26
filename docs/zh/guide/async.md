# 异步支持

## 异步模块

Symphra Modules 原生支持异步模块，无需额外配置：

```python
import asyncio
from symphra_modules.abc import BaseModule, ModuleMetadata

class AsyncModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(name="async_example")

    async def start(self) -> None:
        """异步启动"""
        await asyncio.sleep(1)
        print("异步模块已启动")

    async def stop(self) -> None:
        """异步停止"""
        await asyncio.sleep(0.5)
        print("异步模块已停止")
```

## 自动检测

框架自动检测模块是同步还是异步：

```python
# 同步模块
class SyncModule(BaseModule):
    def start(self) -> None:
        print("同步启动")

# 异步模块
class AsyncModule(BaseModule):
    async def start(self) -> None:
        await asyncio.sleep(1)
        print("异步启动")

# 混合使用
manager = ModuleManager()
await manager.load_from_directory("./modules")  # 自动处理同步和异步模块
```

## 异步生命周期

所有生命周期钩子都支持异步：

```python
class DatabaseModule(BaseModule):
    async def bootstrap(self) -> None:
        """异步初始化"""
        self.pool = await create_connection_pool()

    async def install(self, config: dict | None = None) -> None:
        """异步安装"""
        await super().install(config)
        await self.pool.execute("CREATE TABLE IF NOT EXISTS users...")

    async def start(self) -> None:
        """异步启动"""
        self.server = await start_database_server()

    async def stop(self) -> None:
        """异步停止"""
        await self.server.shutdown()

    async def uninstall(self) -> None:
        """异步卸载"""
        await self.pool.close()
```

## 异步依赖解析

依赖解析支持异步模块：

```python
# 异步依赖检查
await manager.validate_async_dependencies()

# 异步依赖解析
await manager.resolve_async_dependencies()
```

## 异步事件处理

事件系统完全支持异步处理：

```python
from symphra_modules.events import EventBus

bus = EventBus()

@bus.subscribe("async.event")
async def async_handler(data: dict):
    """异步事件处理器"""
    await process_data_async(data)
    await bus.publish("processing.complete", data_id=data["id"])
```

## 并发控制

### 异步批量操作

```python
# 并发启动所有模块
await manager.start_all_concurrent()

# 限制并发数量
await manager.start_all_concurrent(max_concurrency=5)
```

### 异步迭代

```python
# 异步遍历模块
async for module in manager.get_modules_async():
    await module.perform_async_operation()
```

## 异步上下文管理器

模块可以实现异步上下文管理器：

```python
class ResourceModule(BaseModule):
    async def __aenter__(self):
        """异步进入上下文"""
        self.resource = await acquire_resource()
        return self.resource

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步退出上下文"""
        await release_resource(self.resource)
```

## 异步工具函数

框架提供异步工具函数：

```python
from symphra_modules.utils import async_timeout, async_retry

class NetworkModule(BaseModule):
    @async_timeout(30)  # 30秒超时
    async def fetch_data(self, url: str) -> dict:
        """带超时的异步网络请求"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

    @async_retry(max_attempts=3, delay=1.0)  # 重试3次，延迟1秒
    async def unreliable_operation(self) -> None:
        """带重试的不可靠操作"""
        if random.random() < 0.7:  # 70%失败率
            raise ConnectionError("Network error")
        print("Operation succeeded")
```

## 异步测试

编写异步模块的测试：

```python
import pytest
from symphra_modules.testing import AsyncModuleTestCase

class TestAsyncModule(AsyncModuleTestCase):
    async def test_async_start(self):
        """测试异步启动"""
        module = AsyncModule()
        await module.start()
        self.assertTrue(module.is_started)

    async def test_async_event_handling(self):
        """测试异步事件处理"""
        bus = EventBus()
        events_processed = []

        @bus.subscribe("test.async")
        async def handler(data):
            await asyncio.sleep(0.1)  # 模拟异步处理
            events_processed.append(data)

        await bus.publish("test.async", value=42)

        # 等待事件处理完成
        await asyncio.sleep(0.2)
        self.assertEqual(len(events_processed), 1)
        self.assertEqual(events_processed[0]["value"], 42)
```

## 性能考虑

### 异步 vs 同步

```python
# 同步处理（阻塞）
def sync_process_modules(modules):
    for module in modules:
        module.process()  # 每个模块依次处理

# 异步处理（并发）
async def async_process_modules(modules):
    tasks = [module.process_async() for module in modules]
    await asyncio.gather(*tasks)  # 并发处理所有模块
```

### 资源管理

```python
class ConnectionPoolModule(BaseModule):
    async def start(self) -> None:
        # 创建连接池
        self.pool = await create_pool(min_size=5, max_size=20)

    async def stop(self) -> None:
        # 优雅关闭连接池
        await self.pool.close()

    async def get_connection(self):
        """获取连接（带超时）"""
        return await asyncio.wait_for(
            self.pool.acquire(),
            timeout=10.0
        )
```

## 最佳实践

### 避免阻塞操作

```python
# 不推荐：在异步方法中进行阻塞操作
async def bad_example(self):
    # 阻塞文件I/O
    with open("file.txt", "r") as f:
        data = f.read()  # 阻塞！
    return data

# 推荐：使用异步I/O
async def good_example(self):
    # 异步文件I/O
    async with aiofiles.open("file.txt", "r") as f:
        data = await f.read()
    return data
```

### 错误处理

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

### 并发限制

```python
from asyncio import Semaphore

class RateLimitedModule(BaseModule):
    def __init__(self):
        self.semaphore = Semaphore(10)  # 最多10个并发请求

    async def rate_limited_request(self, url: str):
        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.text()
```
