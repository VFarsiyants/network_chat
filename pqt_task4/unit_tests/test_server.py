from email import message
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), '..'))
from server import parse_message
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION,\
    PRESENCE
import unittest


class UnitTestServer(unittest.TestCase):
    """Класс для тестирования функций сервера"""
    def test_parse_message(self):
        """Тетирование разбора корректного сообщения клиента"""
        message = {
            ACTION: PRESENCE,
            TIME: 999999.999999,
            USER: {
                ACCOUNT_NAME: 'Guest'
            }
        }
        self.assertEqual(parse_message(message), {RESPONSE: 200})

    def test_parse_wrong_user(self):
        """Тестирование сообщения от некорректного пользователя"""
        message = {
            ACTION: PRESENCE,
            TIME: 999999.999999,
            USER: {
                ACCOUNT_NAME: 'Not Guest'
            }
        }
        self.assertEqual(parse_message(message), {RESPONSE: 400, 
                                                ERROR: 'Bad Request'})

    def test_parse_incomplete_message(self):
        """Тестирование разбора сообщения с недостающим ключом"""
        message = {
            TIME: 999999.999999,
            USER: {
                ACCOUNT_NAME: 'Not Guest'
            }
        }
        self.assertEqual(parse_message(message), {RESPONSE: 400, 
                                                ERROR: 'Bad Request'})
    
    def test_parse_message_incorrect_presence(self):
        """Тестирование разбора сообщения с неправильным PRESENCE"""
        message = {
            ACTION: "NOT PRESENCE",
            TIME: 999999.999999,
            USER: {
                ACCOUNT_NAME: 'Not Guest'
            }
        }
        self.assertEqual(parse_message(message), {RESPONSE: 400, 
                                                ERROR: 'Bad Request'})
    
    def test_parse_message_without_time(self):
        """Тестирование разбора сообщения без времени"""
        message = {
            ACTION: "NOT PRESENCE",
            USER: {
                ACCOUNT_NAME: 'Not Guest'
            }
        }
        self.assertEqual(parse_message(message), {RESPONSE: 400, 
                                                ERROR: 'Bad Request'})


if __name__ == '__main__':
    unittest.main()
