"""
1. Каждое из слов «разработка», «сокет», «декоратор» представить в строковом 
формате и проверить тип и содержание соответствующих переменных. Затем с 
помощью онлайн-конвертера преобразовать строковые представление в формат 
Unicode и также проверить тип и содержимое переменных.
"""


def __check_content_type_of_vars():
    for key in [key for key in globals().keys() if not key.startswith('__')]:
        print(f'\nПроверка типа и значения переменной {key}')
        val = globals()[key]
        print(val)
        print(type(val), '\n')


if __name__ == '__main__':
    print('Начало работы программы')
    development = 'разработка'
    soket = 'сокет'
    decorator = 'декоратор'
    __check_content_type_of_vars()

    print('Преобразования в онлайн конвертере\n')

    development_encoded = '\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430'
    soket_encoded = '\u0441\u043e\u043a\u0435\u0442'
    decorator_encoded = '\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440'

    __check_content_type_of_vars()
