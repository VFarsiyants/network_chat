"""
Коснтанты 
"""

# Потр применяемый по усолчанию при осуществлении сетевого взаимодействия
from xmlrpc.client import ResponseError


DEFAULT_PORT = 7777

# IP адресс по умолчанию для подключения клиента
DEFAULT_IP_ADRESS = '127.0.0.1'

# Максимальное число одновременных подключений
MAX_CONNECTIONS = 5

# Максимальная длинна сообщений, байты
MAX_PACKAGE_LENGTH = 1024

# Кодировка информационного взаимодействия
ENCODING = 'utf-8'

# Основные ключи для протокола JIM
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account name'

# Дополнительные ключи для протокола JIM
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
