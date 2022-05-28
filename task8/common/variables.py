"""
Коснтанты 
"""

# Потр применяемый по усолчанию при осуществлении сетевого взаимодействия
import logging


DEFAULT_PORT = 7777

# IP адресс по умолчанию для подключения клиента
DEFAULT_IP_ADRESS = '127.0.0.1'

# Максимальное число одновременных подключений
MAX_CONNECTIONS = 5

# Максимальная длинна сообщений, байты
MAX_PACKAGE_LENGTH = 1024

# Кодировка информационного взаимодействия
ENCODING = 'utf-8'

# Уровень логирования
LOG_LEVEL = logging.DEBUG

# Основные ключи для протокола JIM
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account name'
SENDER = 'sender'

# Дополнительные ключи для протокола JIM
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'msg_text'
DESTINATION = 'to'
EXIT = 'exit'
RESPONSE_200 = {RESPONSE: 200}
RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: None
}
