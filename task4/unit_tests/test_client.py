import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), '..'))
from client import create_presence, parse_answer
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION,\
    PRESENCE
import unittest


class UnittestClient(unittest.TestCase):
    """
    Тесты для функций клиента
    """

    def test_create_presence(self):
        """Проверка корректности создания presence сообщения"""
        test_presence = create_presence()
        test_presence[TIME] = 999999.999999
        good_result = {
            ACTION: PRESENCE,
            TIME: 999999.999999,
            USER: {
                ACCOUNT_NAME: 'Guest'
            }
        }
        self.assertEqual(test_presence, good_result)

    def test_parse_reponse_ok(self):
        """Проверка парсинга успешного ответа при правильном формате"""
        answer = {
            RESPONSE: 200
        }
        self.assertEqual(parse_answer(answer), '200 : OK')

    def test_parse_reponse_nok(self):
        """Проверка парсинга неуспешного ответа при правильном формате"""
        answer = {
            RESPONSE: 400,
            ERROR: 'Bad Request'
        }
        self.assertEqual(parse_answer(answer), '400 : Bad Request')

    def test_parse_reponse_unknow_code(self):
        """Проверка парсинга ответа c неизвестным кодом при правильном формате"""
        answer = {
            RESPONSE: 1313,
            ERROR: 'Alilua'
        }
        self.assertEqual(parse_answer(answer), '400 : Alilua')

    def test_parse_reponse_wrong(self):
        """Проверка выбрасывания исключения при неккоректном ответе 
            без RESPONSE сервера"""
        answer = {
            ERROR: 'alilua'
        }
        self.assertRaises(ValueError, parse_answer, answer)

if __name__ == '__main__':
    unittest.main()
