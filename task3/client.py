import sys
import socket
import time
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_PORT, DEFAULT_IP_ADRESS
from common.utils import get_message, send_message


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
    return presence_querry


def parse_answer(message):
    """ Description
    :type message: dict
    :param message: словарь с параметрами полученного сообщения

    :raises: Value Error при неверном формате полученного сообщения

    :rtype: информация о статусе обработке сообщения
    """
    status = message.get(RESPONSE, None)
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
            raise ValueError
    except IndexError:
        server_address = DEFAULT_IP_ADRESS
        server_port = DEFAULT_PORT
    except ValueError:
        print('Недопустимое значени порта')
        sys.exit(1)

    # Построение сокета для обмена

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_address, server_port))
    message_for_server = create_presence()
    send_message(client_socket, message_for_server)
    try:
        answer = parse_answer(get_message(client_socket))
        print(answer)
    except ValueError:
        print('Ошибка при декодировании сообщения')


if __name__ == '__main__':
    main()
