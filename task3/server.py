import socket
import sys
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT
from common.utils import get_message, send_message


def parse_message(message):
    """ Description
    Функция для обработки сообщения клиента
    :type message: dict
    :param message: словарь с параметрами сообщения

    :rtype: dict со статусом обработки сообщения сервером.
    """
    if ACTION in message and message[ACTION] == PRESENCE and USER in message and TIME in message and message[USER][ACCOUNT_NAME] == 'Guest':
        return {RESPONSE: 200}
    return {
        RESPONSE: 400,
        ERROR: 'Bad request'
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
        print('Не указан номер порта')
    except ValueError:
        print('Неверное значение порта')
        sys.exit(1)

    # получение адреса из комманды
    try:
        if '-a' in sys.argv:
            listen_adress = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_adress = ''
    except IndexError:
        print('Не указано значение адресса')
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
            print(f'Получено сообщение от клиента:\n{received_message}')
            response = parse_message(received_message)
            send_message(client, response)
            client.close()
        except ValueError:
            print('Получено некорректное сообщение')
            client.close()


if __name__ == '__main__':
    main()
