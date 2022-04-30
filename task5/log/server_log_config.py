"""Конфигурация логгера сервера"""

from code import interact
import logging
import sys
import os
sys.path.append('../')
from common.variables import LOG_LEVEL

# Получаем текущую директорию и создаем путь до файла логов
PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'server.log')

# Создаем форматтер сообщения логгера
FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

# Потоки вывода логов
STREAM_HANDLER = logging.StreamHandler(sys.stderr)
# Задаем форматтер для потока вывода
STREAM_HANDLER.setFormatter(FORMATTER)
STREAM_HANDLER.setLevel(logging.ERROR)
STREAM_HANDLER.setLevel(logging.ERROR)
# Файловый обработчик логирования
LOG_FILE = logging.FileHandler(PATH, encoding='utf8')
LOG_FILE.setFormatter(FORMATTER)
# Настройки регистратора
LOGGER = logging.getLogger('server')
LOGGER.addHandler(STREAM_HANDLER)
LOGGER.addHandler(LOG_FILE)
LOGGER.setLevel(LOG_LEVEL)

# проверка работоспособности
if __name__ == '__main__':
    LOGGER.info('Info message')
    LOGGER.error('Error message')
    LOGGER.debug('Debug message')
    LOGGER.critical('Critical message')
