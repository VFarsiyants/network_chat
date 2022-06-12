from select import select
import socket
import sys
import os
import logging
import log.server_log_config
import argparse
from common.decorators import log
from common.variables import *
from common.utils import get_message, send_message
from metaclasses import ServerValidator
from descriptors import Port
from server_db import ServerStorage
import threading
import configparser   # https://docs.python.org/3/library/configparser.html

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem

SERVER_LOGGER = logging.getLogger('server')

# Флаг, что был подключён новый пользователь, нужен чтобы не мучать BD
# постоянными запросами на обновление
new_connection = False
conflag_lock = threading.Lock()


@log
def get_port_adress(default_port, default_address):
    """Функция получения параметров порта и адреса из коммандной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_adress = namespace.a
    listen_port = namespace.p
    if listen_port < 1024 or listen_port > 65535:
        SERVER_LOGGER.critical(f'Неверное значение порта')
        sys.exit(1)
    return listen_adress, listen_port


class Server(threading.Thread, metaclass=ServerValidator):
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

        super().__init__()

    def create_socket(self):
        SERVER_LOGGER.info(
            f'Запущен сервер, порт для подключений: {self.port}, '
            f'адрес с которого принимаются подключения: {self.addr}. '
            f'Если адрес не указан, принимаются соединения с любых адресов.')
        # открытие сокета
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.addr, self.port))
        server_socket.settimeout(0.5)

        self.sock = server_socket
        self.sock.listen()

    def run(self):
        self.create_socket()
        while True:
            # Проверяем новые входящие подключения 
            try:
                client, client_address = self.sock.accept()
            except OSError:
                # Если подключений нет, ничего не делаем
                pass
            else:
                SERVER_LOGGER.info(f'Установлено соедение с ПК {client_address}')
                # Добавляем клиент в список для взаимодействия
                self.clients.append(client)
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
                    except OSError:
                        SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                           f'отключился от сервера.')
                        # Удаляем клиента из таблицы подключенных
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.db.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)
            # Если есть сообщения для отправки и ожидающие клиенты, отправляем им сообщение.
            # Обрабатываем наши сообщение
            for message in self.messages:
                try:
                    self.send_to_message(message, w_list)
                except Exception:
                    SERVER_LOGGER.info(f'Потеряна связь с клиентом {message[DESTINATION]}')
                    self.clients.remove(self.names[message[DESTINATION]])
                    self.db.user_logout(message[DESTINATION])
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
        global new_connection
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
                with conflag_lock:
                    new_connection = True
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
            self.db.process_message(
                message[SENDER], message[DESTINATION])
            return

        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.db.user_logout(message[ACCOUNT_NAME])
            SERVER_LOGGER.info(
                f'Клиент {message[ACCOUNT_NAME]} корректно отключился от сервера.')
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            with conflag_lock:
                new_connection = True
            return

        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.db.get_contacts(message[USER])
            send_message(client, response)

        # Если это добавление контакта
        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.db.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        # Если это удаление контакта
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.db.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        # Если это запрос известных пользователей
        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0]
                                   for user in self.db.users_list()]
            send_message(client, response)
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
            SERVER_LOGGER.info(
                f'Пользователю {message[DESTINATION]} отправлено соощение от пользователя {message[SENDER]}')
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
    # Загрузка файла конфигурации сервера
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    # Загрузка параметров командной строки, если нет параметров, то задаём
    # значения по умоланию.
    listen_address, listen_port = get_port_adress(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    # Инициализация базы данных
    database = ServerStorage(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))

    # Создание экземпляра класса - сервера и его запуск:
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    # Создаём графическое окружение для сервера:
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Инициализируем параметры в окна
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    # Функция, обновляющая список подключённых, проверяет флаг подключения, и
    # если надо обновляет список
    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    # Функция, создающая окно со статистикой клиентов
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создающяя окно с настройками сервера.
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    # Запускаем GUI
    server_app.exec_()


if __name__ == '__main__':
    main()
