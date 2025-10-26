"""工具模块."""

from datetime import UTC, datetime

from symphra_modules.utils.logger import Logger, get_logger, set_logger


def now() -> datetime:
    """获取当前 UTC 时间.

    Returns:
        当前 UTC 时间戳
    """
    return datetime.now(UTC)


__all__ = ["Logger", "get_logger", "set_logger", "now"]
