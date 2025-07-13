import sys

from loguru import logger

from Setting import Setting


class MyLog:
    _logger = logger
    _logger.remove()

    if Setting.get('debug'):
        _logger.add(
            sys.stderr,
            format="<lvl>{level: <8}</lvl> | "  # <lvl> 标签自动应用级别颜色
                   "<white>{message}</white>",
            # level="ERROR"
        )

    @classmethod
    def info(cls, *args):
        parts = [str(arg) for arg in args]
        text = ' '.join(parts)
        cls._logger.info(text)

    @classmethod
    def error(cls, *args):
        parts = [str(arg) for arg in args]
        text = ' '.join(parts)
        cls._logger.error(text)

    @classmethod
    def debug(cls, *args):
        parts = [str(arg) for arg in args]
        text = ' '.join(parts)
        cls._logger.debug(text)