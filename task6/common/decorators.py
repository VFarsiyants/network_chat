import logging
import sys


def log(func):
    def log_call(*args, **kwargs):
        logger_name = 'server' if sys.argv[0] == 'server.py' else 'client'
        logger = logging.getLogger(logger_name)
        logger.debug(
            f'Из объемлющей области видимости "{func.__module__}" Вызвана функция "{func.__name__}"\n'
            f'Параметры функции: {args} {kwargs}\n')
        result = func(*args, **kwargs)
        return result
    return log_call
