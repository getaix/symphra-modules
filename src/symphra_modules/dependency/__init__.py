"""依赖解析模块.

导出依赖图和依赖解析器。
"""

from .graph import DependencyGraph
from .resolver import DependencyResolver

__all__ = [
    "DependencyGraph",
    "DependencyResolver",
]
