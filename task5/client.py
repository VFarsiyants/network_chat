import sys
import socket
import time
import logging
import log.client_log_config
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_PORT, DEFAULT_IP_ADRESS
from common.utils import get_message, send_message


CLIENT_LOGGER = logging.getLogger('client')


def create_presence(account_name='Guest'):
    """ Description
    Функция для генерации запроса о присуствии клиента
    :type account_name: str
    :param account_name: Имя клиента

    :rtype: словарь с параметрами запроса
    """
    presence_querry = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {ACCOUNT_NAME}')
    return presence_querry


def parse_answer(message):
    """ Description
    :type message: dict
    :param message: словарь с параметрами полученного сообщения

    :raises: Value Error при неверном формате полученного сообщения

    :rtype: информация о статусе обработке сообщения
    """
    status = message.get(RESPONSE, None)
    CLIENT_LOGGER.debug(f'Обрабтка сообщения от сервера {message}')
    if status:
        if status == 200:
            return '200 : OK'
        return f'400 : {message[ERROR]}'
    raise ValueError


def main():
    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if server_port < 1024 or server_port > 65535:
            CLIENT_LOGGER.error(f'Недопустимое значение порта при запуске клиента: {server_port}')
            raise ValueError
    except IndexError:
        server_address = DEFAULT_IP_ADRESS
        server_port = DEFAULT_PORT
    except ValueError:
        sys.exit(1)

    # Построение сокета для обмена

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_address, server_port))
        message_for_server = create_presence()
        send_message(client_socket, message_for_server)
    except ConnectionRefusedError:
        CLIENT_LOGGER.critical(f'Ошибка при подключении к серверу {server_address}:{server_port}')
    try:
        answer = parse_answer(get_message(client_socket))
        CLIENT_LOGGER.info(f'Получен ответ от сервера {answer}')
    except ValueError:
        CLIENT_LOGGER.error(f'Ошибка при декодировании полученного сообщения')


if __name__ == '__main__':
    main()
