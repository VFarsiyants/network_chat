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
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, MESSAGE, MESSAGE_TEXT, \
        SENDER, DESTINATION, EXIT, RESPONSE_400, RESPONSE_200
from common.utils import get_message, send_message


SERVER_LOGGER = logging.getLogger('server')

@log
def process_client_message(message, messages_list, client, clients, names):
    """
    Обработчик сообщений от клиентов, принимает словарь - сообщение от клинта,
    проверяет корректность, отправляет словарь-ответ для клиента с результатом приёма.
    :param message:
    :param messages_list:
    :param client:
    :return:
    """
    # Если это сообщение о присутствии, принимаем и отвечаем, если успех
    SERVER_LOGGER.debug(f'Разбор сообщения от клиента : {message}')
    # Если это сообщение о присутствии, принимаем и отвечаем
    if ACTION in message and message[ACTION] == PRESENCE and \
            TIME in message and USER in message:
        # Если такой пользователь ещё не зарегистрирован,
        # регистрируем, иначе отправляем ответ и завершаем соединение.
        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = client
            send_message(client, RESPONSE_200)
        else:
            response = RESPONSE_400
            response[ERROR] = 'Имя пользователя уже занято.'
            send_message(client, response)
            clients.remove(client)
            client.close()
        return
    elif ACTION in message and message[ACTION] == MESSAGE and \
            DESTINATION in message and TIME in message \
            and SENDER in message and MESSAGE_TEXT in message:
        messages_list.append(message)
        return
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        clients.remove(names[message[ACCOUNT_NAME]])
        names[message[ACCOUNT_NAME]].close()
        del names[message[ACCOUNT_NAME]]
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
def send_to_message(message, names, listeners):
    """
    Адресная отправка сообщения получателю
    """
    # Если получатель подключен к чату
    if message[DESTINATION] in names and names[message[DESTINATION]] in listeners:
        send_message(names[message[DESTINATION]], message)
        SERVER_LOGGER.info(f'Пользователю {message[DESTINATION]} отправлено соощение от пользователя {message[SENDER]}')
    elif message[DESTINATION] in names and names[message[DESTINATION]] not in listeners:
        raise ConnectionError
    else:
        SERVER_LOGGER.error(
            f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
            f'отправка сообщения невозможна.'
        )



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
    return listen_adress, listen_port

def main():
    # получение порта и адреса из команды
    listen_adress, listen_port = get_port_adress()
    SERVER_LOGGER.info(
        f'Запущен сервер, порт для подключений: {listen_port}, '
        f'адрес с которого принимаются подключения: {listen_adress}. '
        f'Если адрес не указан, принимаются соединения с любых адресов.')
    # открытие сокета
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((listen_adress, listen_port))
    server_socket.settimeout(0.5)
    server_socket.listen(MAX_CONNECTIONS)
    # Словарь client_name -> client_socket
    names = {}
    # Все клиенты и очередь сообщений
    all_clients = []
    messages = []

    while True:
        # Проверяем новые входящие подключения 
        try:
            client, client_address = server_socket.accept()
        except OSError:
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
                                                messages, client_with_message, all_clients, names)
                    except:
                        SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                    f'отключился от сервера.')
                        all_clients.remove(client_with_message)
                    # Если есть сообщения для отправки и ожидающие клиенты, отправляем им сообщение.
            # Обрабатываем наши сообщение
            for message in messages:
                try:
                    send_to_message(message, names, w_list)
                except Exception:
                    SERVER_LOGGER.info(f'Потеряна связь с клиентом {message[DESTINATION]}')
                    all_clients.remove(names[message[DESTINATION]])
                    del names[message[DESTINATION]]
            messages.clear()


if __name__ == '__main__':
    main()
