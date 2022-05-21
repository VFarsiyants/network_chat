import json
from .variables import ENCODING, MAX_PACKAGE_LENGTH
from .decorators import log


@log
def get_message(client):
    """ Description
    Функция декодирования сообщения
    :param client: открытый сокет

    :raises: Вызывает исключение Value Error при неверном формате полученного сообщения

    :return: response: словарь с данными дековдированного сообщения 
    """
    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    try:
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        assert isinstance(response, dict), 'Получен неверный формат сообщения'
        return response
    except:
        raise ValueError


@log
def send_message(sock, message):
    """ Description

    Функция кодирования и отправки сообщения

    :param sock: открытый сокет
    :param message: значения отправляемого сообщения

    :raises: Type Error при неверном формате сообщения
    """
    try:
        assert isinstance(message, dict)
        js_message = json.dumps(message)
        encoded_message = js_message.encode(ENCODING)
        sock.send(encoded_message)
    except:
        raise TypeError
