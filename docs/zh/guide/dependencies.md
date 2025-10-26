# 依赖管理

## 依赖声明

模块可以通过元数据声明依赖关系：

```python
from symphra_modules.abc import BaseModule, ModuleMetadata

class DatabaseModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="database",
            dependencies=[],  # 无依赖
        )

class UserModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="user",
            dependencies=["database"],  # 依赖 database 模块
        )
```

## 依赖类型

### 必需依赖

模块正常工作所需的依赖：

```python
ModuleMetadata(
    name="web_server",
    dependencies=["database", "cache", "logger"]
)
```

### 可选依赖

模块可以选择使用的依赖：

```python
ModuleMetadata(
    name="metrics",
    optional_dependencies=["prometheus", "grafana"]
)
```

## 依赖解析

### 拓扑排序

Symphra Modules 使用 Kahn 算法进行依赖解析：

```python
from symphra_modules.resolver import DependencyResolver

resolver = DependencyResolver()
modules = [db_module, user_module, web_module]

# 解析依赖顺序
ordered_modules = resolver.resolve_dependencies(modules)
# 返回: [db_module, user_module, web_module]
```

### 循环检测

自动检测并报告循环依赖：

```python
# 循环依赖示例（会抛出异常）
# A 依赖 B, B 依赖 A

try:
    ordered_modules = resolver.resolve_dependencies(modules)
except CircularDependencyError as e:
    print(f"循环依赖检测: {e}")
```

## 依赖注入

模块可以通过管理器访问其他模块：

```python
class UserModule(BaseModule):
    def start(self) -> None:
        # 获取依赖的数据库模块
        db_module = self.manager.get_module("database")
        self.db_connection = db_module.get_connection()
```

## 延迟依赖

支持运行时动态添加依赖：

```python
# 运行时添加依赖
await manager.add_dependency("user_module", "cache_module")

# 重新解析依赖
await manager.resolve_all_dependencies()
```

## 版本约束

支持版本范围的依赖声明：

```python
ModuleMetadata(
    name="api_client",
    dependencies=["database>=1.0.0,<2.0.0"]
)
```

## 依赖验证

启动前验证所有依赖是否满足：

```python
# 验证依赖
missing_deps = manager.validate_dependencies()
if missing_deps:
    print(f"缺少依赖: {missing_deps}")
    # 处理缺失依赖
```

## 最佳实践

### 依赖分层

- **基础层**: 数据库、缓存、配置
- **服务层**: 业务逻辑模块
- **接口层**: API、Web界面

### 避免循环依赖

- 使用事件系统替代直接依赖
- 提取公共接口到独立模块
- 使用依赖注入模式

### 可选依赖处理

```python
class MonitoringModule(BaseModule):
    def start(self) -> None:
        # 检查可选依赖
        if self.manager.has_module("prometheus"):
            prometheus = self.manager.get_module("prometheus")
            # 使用 prometheus 模块
        else:
            # 使用备用方案
            self.logger.warning("Prometheus not available, using basic monitoring")
```

### 依赖测试

```python
# 单元测试中的依赖模拟
import pytest
from unittest.mock import Mock

def test_user_module():
    mock_db = Mock()
    manager = Mock()
    manager.get_module.return_value = mock_db

    user_module = UserModule()
    user_module.manager = manager
    user_module.start()

    # 验证依赖调用
    manager.get_module.assert_called_with("database")
```
