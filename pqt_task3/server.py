from select import select
import socket
import sys
import logging
import log.server_log_config
import argparse
from common.decorators import log
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, MESSAGE, MESSAGE_TEXT, \
        SENDER, DESTINATION, EXIT, RESPONSE_400, RESPONSE_200
from common.utils import get_message, send_message
from metaclasses import ServerValidator
from descriptors import Port
from server_db import ServerStorage


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


SERVER_LOGGER = logging.getLogger('server')

class Server(metaclass=ServerValidator):
    port = Port()

    def __init__(self, listen_address, listen_port, db):
        # Параметры подключения
        self.addr = listen_address
        self.port = listen_port

        # Список подключённых клиентов.
        self.clients = []

        # Список сообщений на отправку.
        self.messages = []

        # Словарь содержащий сопоставленные имена и соответствующие им сокеты.
        self.names = dict()

        self.db = db

    def create_socket(self):
        SERVER_LOGGER.info(
        f'Запущен сервер, порт для подключений: {self.port}, '
        f'адрес с которого принимаются подключения: {self.addr}. '
        f'Если адрес не указан, принимаются соединения с любых адресов.')
        # открытие сокета
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.addr, self.port))
        self.server_socket.settimeout(0.5)
        self.server_socket.listen(MAX_CONNECTIONS)

    def main_loop(self):
        self.create_socket()
        while True:
            # Проверяем новые входящие подключения 
            try:
                client, client_address = self.server_socket.accept()
            except OSError:
            # Если подключений нет, ничего не делаем
                pass
            else:
                SERVER_LOGGER.info(f'Установлено соедение с ПК {client_address}')
                # Добавляем клиент в список для взаимодействия
                self.clients.append(client)
            finally:
                # Список сокетов ожидающих чтения (read)
                r_list = []
                # Список сокетов ожидающих ответа (write)
                w_list = []
                try:
                    if self.clients:
                        r_list, w_list, e_list = select(self.clients, self.clients, [], 0)
                except OSError:
                    pass
                if r_list:
                    for client_with_message in r_list:
                        try:
                            self.process_client_message(get_message(client_with_message), client_with_message)
                        except:
                            SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                        f'отключился от сервера.')
                            self.clients.remove(client_with_message)
                        # Если есть сообщения для отправки и ожидающие клиенты, отправляем им сообщение.
                # Обрабатываем наши сообщение
                for message in self.messages:
                    try:
                        self.send_to_message(message, w_list)
                    except Exception:
                        SERVER_LOGGER.info(f'Потеряна связь с клиентом {message[DESTINATION]}')
                        self.clients.remove(self.names[message[DESTINATION]])
                        del self.names[message[DESTINATION]]
                self.messages.clear()

    @log
    def process_client_message(self, message, client):
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
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.db.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Имя пользователя уже занято.'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        elif ACTION in message and message[ACTION] == MESSAGE and \
                DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            self.messages.append(message)
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.db.user_logout(message[ACCOUNT_NAME])
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            return
        # Иначе отдаём Bad request
        else:
            send_message(client, {
                RESPONSE: 400,
                ERROR: 'Bad Request'
            })
            return
    
    @log
    def send_to_message(self, message, listeners):
        """
        Адресная отправка сообщения получателю
        """
        # Если получатель подключен к чату
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listeners:
            send_message(self.names[message[DESTINATION]], message)
            SERVER_LOGGER.info(f'Пользователю {message[DESTINATION]} отправлено соощение от пользователя {message[SENDER]}')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listeners:
            raise ConnectionError
        else:
            SERVER_LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.'
            )

# @log
# def parse_message(message):
#     """ Description
#     Функция для обработки сообщения клиента
#     :type message: dict
#     :param message: словарь с параметрами сообщения

#     :rtype: dict со статусом обработки сообщения сервером.
#     """
#     SERVER_LOGGER.debug('Обработка сообщения от клиента')
#     if ACTION in message and message[ACTION] == PRESENCE and USER in message \
#         and TIME in message and message[USER][ACCOUNT_NAME] == 'Guest':
#         SERVER_LOGGER.info(f'Получено сообщение от клиента ${message}')
#         return {RESPONSE: 200}
#     SERVER_LOGGER.error(f'Получено сообщение в неправильном формате {message}')
#     return {
#         RESPONSE: 400,
#         ERROR: 'Bad Request'
#     }


def main():
    # получение порта и адреса из команды
    listen_adress, listen_port = get_port_adress()

    db = ServerStorage()

    server = Server(listen_adress, listen_port, db)
    server.main_loop()


if __name__ == '__main__':
    main()
