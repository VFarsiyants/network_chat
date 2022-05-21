from select import select
import socket
import sys
import logging
from urllib import request
import log.server_log_config
import argparse
import time
from common.decorators import log
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, ENCODING, MESSAGE, MESSAGE_TEXT, \
        SENDER
from common.utils import get_message, send_message


SERVER_LOGGER = logging.getLogger('server')

@log
def process_client_message(message, messages_list, client):
    """
    Обработчик сообщений от клиентов, принимает словарь - сообщение от клинта,
    проверяет корректность, отправляет словарь-ответ для клиента с результатом приёма.
    :param message:
    :param messages_list:
    :param client:
    :return:
    """
    SERVER_LOGGER.debug(f'Разбор сообщения от клиента : {message}')
    # Если это сообщение о присутствии, принимаем и отвечаем, если успех
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
            and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
        send_message(client, {RESPONSE: 200})
        return
    # Если это сообщение, то добавляем его в очередь сообщений. Ответ не требуется.
    elif ACTION in message and message[ACTION] == MESSAGE and \
            TIME in message and MESSAGE_TEXT in message:
        messages_list.append((message[ACCOUNT_NAME], message[MESSAGE_TEXT]))
        return
    # Иначе отдаём Bad request
    else:
        send_message(client, {
            RESPONSE: 400,
            ERROR: 'Bad Request'
        })
        return

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


@log
def get_port_adress():
    """Функция получения параметров порта и адреса из коммандной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_adress = namespace.a
    listen_port = namespace.p
    if listen_port < 1024 or listen_port > 65535:
        SERVER_LOGGER.critical(f'Неверное значение порта')
        sys.exit(1)
    return namespace.a, namespace.p

def main():
    # получение порта и адреса из команды
    listen_adress, listen_port = get_port_adress()

    # открытие сокета
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((listen_adress, listen_port))
    server_socket.settimeout(0.2)
    server_socket.listen(MAX_CONNECTIONS)

    # Все клиенты и очередь сообщений
    all_clients = []
    messages = []

    while True:
        # Проверяем новые входящие подключения 
        try:
            client, client_address = server_socket.accept()
        except OSError as error:
        # Если подключений нет, ничего не делаем
            pass
        else:
            SERVER_LOGGER.info(f'Установлено соедение с ПК {client_address}')
            # Добавляем клиент в список для взаимодействия
            all_clients.append(client)
        finally:
            # Список сокетов ожидающих чтения (read)
            r_list = []
            # Список сокетов ожидающих ответа (write)
            w_list = []
            try:
                if all_clients:
                    r_list, w_list, e_list = select(all_clients, all_clients, [], 0)
            except OSError:
                pass
            if r_list:
                for client_with_message in r_list:
                    try:
                        process_client_message(get_message(client_with_message),
                                                messages, client_with_message)
                    except:
                        SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                    f'отключился от сервера.')
                        all_clients.remove(client_with_message)
                    # Если есть сообщения для отправки и ожидающие клиенты, отправляем им сообщение.
                    if messages and w_list:
                        message = {
                            ACTION: MESSAGE,
                            SENDER: messages[0][0],
                            TIME: time.time(),
                            MESSAGE_TEXT: messages[0][1]
                        }
                        del messages[0]
                        for waiting_client in w_list:
                            try:
                                send_message(waiting_client, message)
                            except:
                                SERVER_LOGGER.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                                waiting_client.close()
                                all_clients.remove(waiting_client)
                        



if __name__ == '__main__':
    main()
