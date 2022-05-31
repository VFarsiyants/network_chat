import sys
import socket
import threading
import time
import argparse
import logging
import log.client_log_config
import json
from common.decorators import log
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_PORT, DEFAULT_IP_ADRESS, MESSAGE, MESSAGE_TEXT, \
        SENDER, EXIT, DESTINATION
from common.utils import get_message, send_message
from metaclasses import ClientValidation
from errors import NoMesage


CLIENT_LOGGER = logging.getLogger('client')


class ClientSender(threading.Thread, metaclass=ClientValidation):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()
    
    @log
    def create_exit_message(self):
        """
        Функция для отправкии сообщения о выходе на сервер
        """
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    @log
    def create_message(self):
        """Функция запрашивает текст сообщения и возвращает его.
        Так же завершает работу при вводе подобной комманды
        """
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        if message == '\q':
            self.sock.close()
            CLIENT_LOGGER.info('Выход по команде пользователя.')
            print('Работа завершена!')
            sys.exit(0)
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
        except Exception as e:
            print(e)
            CLIENT_LOGGER.critical('Потеряно соединение с сервером.')
            sys.exit(1)

    def print_help(self):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    def run(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                try:
                    send_message(self.sock, self.create_exit_message())
                except:
                    pass
                print('Завершение соединения.')
                CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')


class ClientReader(threading.Thread , metaclass=ClientValidation):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def run(self):
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name:
                    print(f'\nПолучено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                    CLIENT_LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                else:
                    CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
            except NoMesage:
                pass
            except ValueError:
                CLIENT_LOGGER.error(f'Не удалось декодировать полученное сообщение.')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                break


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
def message_from_server(sock, my_name):
    """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
    while True:
        try:
            message = get_message(sock)
            if ACTION in message and message[ACTION] == MESSAGE and \
                    SENDER in message and MESSAGE_TEXT in message and \
                        DESTINATION in message and message[DESTINATION] == my_name:
                print(f'Получено сообщение от пользователя:'
                    f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                CLIENT_LOGGER.info(f'Получено сообщение от пользователя '
                            f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
            else:
                CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
        except Exception:
            CLIENT_LOGGER.error(f'Произошла ошибка при получении сообщений.')
            break


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
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        CLIENT_LOGGER.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    return server_address, server_port, client_name


def main():
    server_address, server_port, client_name = arg_parser()

    """Сообщаем о запуске"""
    print(f'Консольный месседжер. Клиентский модуль. Имя пользователя: {client_name}')

    # Если имя пользователя не было задано, необходимо запросить пользователя.
    if not client_name:
        client_name = input('Введите имя пользователя: ')

    CLIENT_LOGGER.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, имя пользователя: {client_name}')
    # Построение сокета для обмена

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_address, server_port))
        message_for_server = create_presence(client_name)
        send_message(client_socket, message_for_server)
        answer = parse_answer(get_message(client_socket))
        CLIENT_LOGGER.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')

    except ConnectionRefusedError:
        CLIENT_LOGGER.critical(f'Ошибка при подключении к серверу {server_address}:{server_port}')
        sys.exit(1)
    # Если соединение с сервером установлено корректно,
    # начинаем обмен с ним, согласно требуемому режиму.
    # основной цикл прогрммы:
    # запускаем процесс получения сообщений
    receiv_process = ClientReader(client_name, client_socket)
    receiv_process.daemon = True
    receiv_process.start()
    # запускаем процесс отправки сообщений
    send_proces = ClientSender(client_name, client_socket)
    send_proces.daemon = True
    send_proces.start()
    CLIENT_LOGGER.debug('Запущены процессы')

    # Клиент активен пока работают оба процесса
    # Если один из процессов завершен, программа завершается
    while True:
        time.sleep(1)
        if receiv_process.is_alive() and send_proces.is_alive():
            continue
        break




if __name__ == '__main__':
    main()