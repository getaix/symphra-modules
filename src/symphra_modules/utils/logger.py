"""抽象日志接口."""

import logging
from typing import Any, Protocol


class Logger(Protocol):
    """日志记录器协议.

    定义了日志接口,用户可以提供自己的日志实现。
    """

    def debug(self, message: str, **kwargs: Any) -> None:
        """记录 DEBUG 级别日志."""
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        """记录 INFO 级别日志."""
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """记录 WARNING 级别日志."""
        ...

    def error(self, message: str, **kwargs: Any) -> None:
        """记录 ERROR 级别日志."""
        ...

    def exception(self, message: str, **kwargs: Any) -> None:
        """记录异常信息."""
        ...


class StandardLogger:
    """基于 Python 标准库 logging 的默认日志实现."""

    def __init__(self, name: str = "symphra_modules") -> None:
        """初始化日志记录器.

        Args:
            name: 日志记录器名称
        """
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def debug(self, message: str, **kwargs: Any) -> None:
        """记录 DEBUG 级别日志."""
        self._logger.debug(self._format_message(message, kwargs))

    def info(self, message: str, **kwargs: Any) -> None:
        """记录 INFO 级别日志."""
        self._logger.info(self._format_message(message, kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        """记录 WARNING 级别日志."""
        self._logger.warning(self._format_message(message, kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        """记录 ERROR 级别日志."""
        self._logger.error(self._format_message(message, kwargs))

    def exception(self, message: str, **kwargs: Any) -> None:
        """记录异常信息."""
        self._logger.exception(self._format_message(message, kwargs))

    def _format_message(self, message: str, kwargs: dict[str, Any]) -> str:
        """格式化日志消息.

        Args:
            message: 消息模板
            kwargs: 格式化参数

        Returns:
            格式化后的消息
        """
        if kwargs:
            try:
                return message.format(**kwargs)
            except (KeyError, ValueError):
                # 如果格式化失败，附加 kwargs 信息
                return f"{message} | {kwargs}"
        return message


# 全局日志实例
_global_logger: Logger = StandardLogger()


def get_logger() -> Logger:
    """获取全局日志实例.

    Returns:
        当前配置的日志记录器
    """
    return _global_logger


def set_logger(logger: Logger) -> None:
    """设置全局日志实例.

    Args:
        logger: 新的日志记录器实例
    """
    global _global_logger
    _global_logger = logger
