# 事件系统

## 事件总线

Symphra Modules 提供灵活的事件驱动架构：

```python
from symphra_modules.events import EventBus

# 创建事件总线
bus = EventBus()

# 发布事件
await bus.publish("user.created", user_id=123, email="user@example.com")

# 订阅事件
@bus.subscribe("user.created")
async def handle_user_created(user_id: int, email: str):
    print(f"New user: {user_id} - {email}")
```

## 事件类型

### 模块生命周期事件

```python
# 模块状态变化事件
bus.subscribe("module.state_changed", handler)

# 模块加载完成事件
bus.subscribe("module.loaded", handler)

# 模块启动事件
bus.subscribe("module.started", handler)
```

### 自定义业务事件

```python
# 业务逻辑事件
bus.publish("order.placed", order_id="123", amount=99.99)
bus.publish("payment.processed", order_id="123", status="success")
```

## 订阅模式

### 直接订阅

```python
# 订阅特定事件
bus.subscribe("user.login", login_handler)

# 订阅所有事件
bus.subscribe("*", all_events_handler)
```

### 模式匹配

```python
# 订阅 user.* 模式
bus.subscribe("user.*", user_events_handler)

# 订阅 *.error 模式
bus.subscribe("*.error", error_handler)
```

### 条件订阅

```python
# 基于条件订阅
bus.subscribe(
    "order.*",
    order_handler,
    condition=lambda event: event.data.get("amount", 0) > 100
)
```

## 异步处理

所有事件处理都支持异步：

```python
@bus.subscribe("data.process")
async def async_processor(data: dict):
    # 异步处理数据
    await process_data_async(data)
    # 发送完成事件
    await bus.publish("data.processed", data_id=data["id"])
```

## 错误隔离

单个处理器异常不会影响其他处理器：

```python
@bus.subscribe("user.action")
def handler1(event):
    # 正常处理
    pass

@bus.subscribe("user.action")
def handler2(event):
    # 抛出异常
    raise ValueError("Something went wrong")

# handler1 仍然会执行
```

## 事件数据

### 结构化事件

```python
from symphra_modules.events import Event

# 创建结构化事件
event = Event(
    name="user.registered",
    data={
        "user_id": 123,
        "email": "user@example.com",
        "timestamp": datetime.now()
    },
    metadata={
        "source": "auth_module",
        "version": "1.0"
    }
)

await bus.publish_event(event)
```

### 事件过滤

```python
# 过滤事件
filtered_events = bus.filter_events(
    event_name="user.*",
    condition=lambda e: e.data.get("active", True)
)
```

## 事件历史

记录和查询事件历史：

```python
# 获取最近事件
recent_events = bus.get_recent_events(limit=10)

# 查询特定事件
user_events = bus.query_events(
    name="user.*",
    start_time=datetime.now() - timedelta(hours=1)
)
```

## 性能优化

### 事件缓冲

```python
# 启用事件缓冲
bus.enable_buffering(buffer_size=100, flush_interval=1.0)

# 手动刷新缓冲
await bus.flush_buffer()
```

### 异步发布

```python
# 异步发布，不等待处理完成
await bus.publish_async("log.entry", message="System started")

# 批量发布
await bus.publish_batch([
    {"name": "metric.cpu", "value": 85},
    {"name": "metric.memory", "value": 72},
])
```

## 最佳实践

### 事件命名约定

- 使用点号分隔命名空间: `module.action`
- 使用过去时表示已完成事件: `user.created`, `order.cancelled`
- 使用通配符进行分类: `auth.*`, `payment.*`

### 错误处理

```python
@bus.subscribe("system.error")
async def error_handler(event):
    try:
        # 处理错误
        await handle_error(event.data)
    except Exception as e:
        # 记录处理失败，但不抛出异常
        logger.error(f"Failed to handle error event: {e}")
```

### 事件链

避免事件处理中发布新事件导致的无限循环：

```python
# 不推荐：可能导致循环
@bus.subscribe("user.updated")
def update_handler(event):
    # 这可能触发另一个 user.updated 事件
    user.save()
    bus.publish("user.updated", user=user)

# 推荐：使用不同事件名
@bus.subscribe("user.update_requested")
def update_handler(event):
    user.save()
    bus.publish("user.updated", user=user)
```

### 测试事件

```python
import pytest

def test_event_publishing():
    bus = EventBus()

    events_received = []

    @bus.subscribe("test.event")
    def handler(data):
        events_received.append(data)

    # 发布测试事件
    bus.publish("test.event", message="test")

    # 验证事件被处理
    assert len(events_received) == 1
    assert events_received[0]["message"] == "test"
```
