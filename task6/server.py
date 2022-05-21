import socket
import sys
import logging
import log.server_log_config
from common.decorators import log
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT
from common.utils import get_message, send_message


SERVER_LOGGER = logging.getLogger('server')

@log
def parse_message(message):
    """ Description
    Функция для обработки сообщения клиента
    :type message: dict
    :param message: словарь с параметрами сообщения

    :rtype: dict со статусом обработки сообщения сервером.
    """
    SERVER_LOGGER.debug('Обработка сообщения от клиента')
    if ACTION in message and message[ACTION] == PRESENCE and USER in message \
        and TIME in message and message[USER][ACCOUNT_NAME] == 'Guest':
        SERVER_LOGGER.info(f'Получено сообщение от клиента ${message}')
        return {RESPONSE: 200}
    SERVER_LOGGER.error(f'Получено сообщение в неправильном формате {message}')
    return {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }


def main():
    # получение порта из команды
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_PORT
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        SERVER_LOGGER.critical(f'Не указан номер порта')
    except ValueError:
        SERVER_LOGGER.critical(f'Неверное значение порта')
        sys.exit(1)

    # получение адреса из комманды
    try:
        if '-a' in sys.argv:
            listen_adress = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_adress = ''
    except IndexError:
        SERVER_LOGGER.critical(f'Не указано значение адреса')
        sys.exit(1)

    # открытие сокета
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((listen_adress, listen_port))

    server_socket.listen(MAX_CONNECTIONS)

    while True:
        client, client_address = server_socket.accept()
        try:
            received_message = get_message(client)
            SERVER_LOGGER.info(f'Получено сообщение от клиента:\n{received_message}')
            response = parse_message(received_message)
            SERVER_LOGGER.info(f'Отправляем ответ клиенту:\n{response}')
            send_message(client, response)
            client.close()
        except ValueError:
            SERVER_LOGGER.error(f'От клиента получено неккоректное сообщение')
            client.close()


if __name__ == '__main__':
    main()
