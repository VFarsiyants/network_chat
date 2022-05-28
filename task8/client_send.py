import sys
import socket
import time
import argparse
import logging
import log.client_log_config
from common.decorators import log
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_PORT, DEFAULT_IP_ADRESS, MESSAGE, MESSAGE_TEXT, \
        SENDER
from common.utils import get_message, send_message


CLIENT_LOGGER = logging.getLogger('client')


@log
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

@log
def message_from_server(message):
    """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
    if ACTION in message and message[ACTION] == MESSAGE and \
            SENDER in message and MESSAGE_TEXT in message:
        print(f'Получено сообщение от пользователя '
              f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
        CLIENT_LOGGER.info(f'Получено сообщение от пользователя '
                    f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
    else:
        CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')

@log
def create_message(sock, account_name='Guest'):
    """Функция запрашивает текст сообщения и возвращает его.
    Так же завершает работу при вводе подобной комманды
    """
    message = input('Введите сообщение для отправки или \'\q\' для завершения работы: ')
    if message == '\q':
        sock.close()
        CLIENT_LOGGER.info('Выход по команде пользователя.')
        print('Работа завершена!')
        sys.exit(0)
    message_dict = {
        ACTION: MESSAGE,
        TIME: time.time(),
        ACCOUNT_NAME: account_name,
        MESSAGE_TEXT: message
    }
    CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
    return message_dict


@log
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

@log
def arg_parser():
    """Создаём парсер аргументов коммандной строки
    и читаем параметры, возвращаем 3 параметра
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-m', '--mode', default='send', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_mode = namespace.mode

    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        CLIENT_LOGGER.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    # Проверим допустим ли выбранный режим работы клиента
    if client_mode not in ('listen', 'send'):
        CLIENT_LOGGER.critical(f'Указан недопустимый режим работы {client_mode}, '
                        f'допустимые режимы: listen , send')
        sys.exit(1)

    return server_address, server_port, client_mode


def main():
    server_address, server_port, client_mode = arg_parser()

    CLIENT_LOGGER.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, режим работы: {client_mode}')
    # Построение сокета для обмена

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_address, server_port))
        message_for_server = create_presence()
        send_message(client_socket, message_for_server)
    except ConnectionRefusedError:
        CLIENT_LOGGER.critical(f'Ошибка при подключении к серверу {server_address}:{server_port}')
        sys.exit(1)
    try:
        answer = parse_answer(get_message(client_socket))
        CLIENT_LOGGER.info(f'Получен ответ от сервера {answer}')
    except ValueError:
        CLIENT_LOGGER.error(f'Ошибка при декодировании полученного сообщения')
    # Если соединение с сервером установлено корректно,
    # начинаем обмен с ним, согласно требуемому режиму.
    # основной цикл прогрммы:
    if client_mode == 'send':
        print('Режим работы - отправка сообщений.')
    else:
        print('Режим работы - приём сообщений.')
    while True:
        # режим работы - отправка сообщений
        if client_mode == 'send':
            try:
                send_message(client_socket, create_message(client_socket))
            except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                CLIENT_LOGGER.error(f'Соединение с сервером {server_address} было потеряно.')
                sys.exit(1)

        # Режим работы приём:
        if client_mode == 'listen':
            try:
                message_from_server(get_message(client_socket))
            except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                CLIENT_LOGGER.error(f'Соединение с сервером {server_address} было потеряно.')
                sys.exit(1)


if __name__ == '__main__':
    main()