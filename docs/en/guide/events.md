# Event System

## Event Bus

Symphra Modules provides a flexible event-driven architecture:

```python
from symphra_modules.events import EventBus

# Create event bus
bus = EventBus()

# Publish event
await bus.publish("user.created", user_id=123, email="user@example.com")

# Subscribe to event
@bus.subscribe("user.created")
async def handle_user_created(user_id: int, email: str):
    print(f"New user: {user_id} - {email}")
```

## Event Types

### Module Lifecycle Events

```python
# Module state change events
bus.subscribe("module.state_changed", handler)

# Module loaded events
bus.subscribe("module.loaded", handler)

# Module started events
bus.subscribe("module.started", handler)
```

### Custom Business Events

```python
# Business logic events
bus.publish("order.placed", order_id="123", amount=99.99)
bus.publish("payment.processed", order_id="123", status="success")
```

## Subscription Patterns

### Direct Subscription

```python
# Subscribe to specific event
bus.subscribe("user.login", login_handler)

# Subscribe to all events
bus.subscribe("*", all_events_handler)
```

### Pattern Matching

```python
# Subscribe to user.* pattern
bus.subscribe("user.*", user_events_handler)

# Subscribe to *.error pattern
bus.subscribe("*.error", error_handler)
```

### Conditional Subscription

```python
# Subscribe based on conditions
bus.subscribe(
    "order.*",
    order_handler,
    condition=lambda event: event.data.get("amount", 0) > 100
)
```

## Async Processing

All event handling supports async:

```python
@bus.subscribe("data.process")
async def async_processor(data: dict):
    # Process data asynchronously
    await process_data_async(data)
    # Send completion event
    await bus.publish("data.processed", data_id=data["id"])
```

## Error Isolation

Exceptions in single handlers won't affect other handlers:

```python
@bus.subscribe("user.action")
def handler1(event):
    # Normal processing
    pass

@bus.subscribe("user.action")
def handler2(event):
    # Throws exception
    raise ValueError("Something went wrong")

# handler1 will still execute
```

## Event Data

### Structured Events

```python
from symphra_modules.events import Event

# Create structured event
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

### Event Filtering

```python
# Filter events
filtered_events = bus.filter_events(
    event_name="user.*",
    condition=lambda e: e.data.get("active", True)
)
```

## Event History

Record and query event history:

```python
# Get recent events
recent_events = bus.get_recent_events(limit=10)

# Query specific events
user_events = bus.query_events(
    name="user.*",
    start_time=datetime.now() - timedelta(hours=1)
)
```

## Performance Optimization

### Event Buffering

```python
# Enable event buffering
bus.enable_buffering(buffer_size=100, flush_interval=1.0)

# Manually flush buffer
await bus.flush_buffer()
```

### Async Publishing

```python
# Publish asynchronously, don't wait for completion
await bus.publish_async("log.entry", message="System started")

# Batch publishing
await bus.publish_batch([
    {"name": "metric.cpu", "value": 85},
    {"name": "metric.memory", "value": 72},
])
```

## Best Practices

### Event Naming Conventions

- Use dots to separate namespaces: `module.action`
- Use past tense for completed events: `user.created`, `order.cancelled`
- Use wildcards for categorization: `auth.*`, `payment.*`

### Error Handling

```python
@bus.subscribe("system.error")
async def error_handler(event):
    try:
        # Handle error
        await handle_error(event.data)
    except Exception as e:
        # Log handling failure, but don't throw exception
        logger.error(f"Failed to handle error event: {e}")
```

### Event Chains

Avoid infinite loops caused by publishing new events in handlers:

```python
# Not recommended: may cause loops
@bus.subscribe("user.updated")
def update_handler(event):
    # This may trigger another user.updated event
    user.save()
    bus.publish("user.updated", user=user)

# Recommended: use different event names
@bus.subscribe("user.update_requested")
def update_handler(event):
    user.save()
    bus.publish("user.updated", user=user)
```

### Testing Events

```python
import pytest

def test_event_publishing():
    bus = EventBus()

    events_received = []

    @bus.subscribe("test.event")
    def handler(data):
        events_received.append(data)

    # Publish test event
    bus.publish("test.event", message="test")

    # Verify event was processed
    assert len(events_received) == 1
    assert events_received[0]["message"] == "test"
```