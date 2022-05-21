import sys
import os
import unittest
import json
sys.path.insert(0, os.path.join(os.getcwd(), '..'))
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION,\
    PRESENCE, ENCODING
from common.utils import get_message, send_message


class TestSocket:
    """Класс имитирующий поведение сокета"""
    def __init__(self, test_message: str):
        # то, что сокет получает
        self.test_message = test_message
    
    #Сокет должен получать байты при отправке
    def send(self, message_to_send: bytes):
        self.encoded_message = message_to_send

    #То что получаем из сокета при получении поток байтов сериализованного
    # в json словаря.
    def recv(self, max_len):
        return json.dumps(self.test_message).encode(ENCODING)


class TestUtils(unittest.TestCase):

    test_message = {
        ACTION: PRESENCE,
        TIME: 999999.999999,
        USER: {
            ACCOUNT_NAME: 'test_user'
        } 
    }
    wrong_test_message = ['Action', 'Time']
    response_ok = {RESPONSE: 200}
    response_nok = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

    def test_send_message_true(self):
        """Тестирование корректной отправки сообщения. Метод отправки должен
        сформировать в сокете поток байтов сериализованого json словаря"""
        test_socket = TestSocket(self.test_message)
        send_message(test_socket, self.test_message)
        sent_bytes = json.dumps(self.test_message).encode(ENCODING)
        self.assertEqual(test_socket.encoded_message, 
                        sent_bytes)

    def test_send_message_error(self):
        """Тестирование неправильного сообщение, методе отправки должен
        выбросить исключение если сообщение не словарь"""
        test_socket = TestSocket(self.wrong_test_message)
        self.assertRaises(TypeError, send_message, test_socket, 
                        self.wrong_test_message)
    
    def test_response_ok(self):
        """Тестирование получения сообщения. При получении функция получает 
        поток байтов из сокета и формирует из них словарь"""
        test_socket = TestSocket(self.response_ok)
        self.assertEqual(get_message(test_socket), self.response_ok)

    def test_response_nok(self):
        """Тест расшифровки ответа об ошибке"""
        test_socket = TestSocket(self.response_nok)
        self.assertEqual(get_message(test_socket), self.response_nok)

if __name__ == '__main__':
    unittest.main()


