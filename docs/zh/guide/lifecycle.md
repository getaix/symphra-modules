# 生命周期管理

## 模块状态机

Symphra Modules 使用状态机来管理模块的生命周期，确保模块按照正确的顺序启动和停止。

### 状态转换图

```
NOT_INSTALLED → LOADED → INSTALLED → STARTED
     ↑            ↑         ↑          ↑
     └────────────┴─────────┴──────────┘
                    ↓
                 STOPPED
                    ↓
                  ERROR
```

### 状态说明

- **NOT_INSTALLED**: 模块未安装，这是初始状态
- **LOADED**: 模块已加载到注册表中
- **INSTALLED**: 模块已安装并配置完成
- **STARTED**: 模块正在运行
- **STOPPED**: 模块已停止
- **ERROR**: 模块处于错误状态

## 生命周期钩子

### bootstrap()

在模块注册到注册表时调用，用于初始化模块的基本信息。

```python
def bootstrap(self) -> None:
    """初始化模块基本信息"""
    self.logger = logging.getLogger(self.metadata.name)
```

### install(config)

安装模块时调用，接收配置参数并进行必要的设置。

```python
def install(self, config: dict | None = None) -> None:
    """安装模块"""
    super().install(config)
    # 验证配置
    if not self.validate_config(config):
        raise ValueError("Invalid configuration")
    # 保存配置
    self._config = config or {}
```

### start()

启动模块时调用，开始模块的功能。

```python
def start(self) -> None:
    """启动模块"""
    # 启动服务
    self.server.start()
    self.logger.info("Module started")
```

### stop()

停止模块时调用，清理资源。

```python
def stop(self) -> None:
    """停止模块"""
    # 停止服务
    self.server.stop()
    self.logger.info("Module stopped")
```

### uninstall()

卸载模块时调用，清理所有资源。

```python
def uninstall(self) -> None:
    """卸载模块"""
    # 清理资源
    self.server = None
    self._config = None
```

### reload()

热重载模块时调用，用于运行时更新模块。

```python
def reload(self) -> None:
    """重载模块"""
    self.stop()
    # 重新加载配置或代码
    self.start()
```

## 批量操作

ModuleManager 支持批量生命周期操作：

```python
# 批量启动所有模块
await manager.start_all()

# 批量停止所有模块
await manager.stop_all()

# 按依赖顺序启动
await manager.start_modules(["module_a", "module_b"])
```

## 错误处理

生命周期操作中的异常会被捕获并转换为 ERROR 状态：

```python
try:
    await module.start()
except Exception as e:
    module.state = ModuleState.ERROR
    module.error = e
    raise ModuleLifecycleError(f"Failed to start module {module.metadata.name}") from e
```

## 异步支持

所有生命周期钩子都支持异步实现：

```python
async def start(self) -> None:
    """异步启动模块"""
    await self.database.connect()
    await self.cache.warmup()
```