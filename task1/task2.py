"""
2. Каждое из слов «class», «function», «method» записать в байтовом типе без 
преобразования в последовательность кодов (не используя методы encode и decode) 
и определить тип, содержимое и длину соответствующих переменных.
"""


def to_bytes(*args):
    for arg in args:
        print('*' * 80)
        print(f'Преобразуем и проверяем слово "{arg}"')
        try:
            arg_bytes = eval(f'b\'{arg}\'')
        except:
            print(f'Невозможно привести к байтовому типу')
            return
        print(f'Слово {arg} в байтовом типе - {arg_bytes}')
        print(f'Тип байтового типа - {type(arg_bytes)}')
        bytes_num = len(arg_bytes)
        print(f'Число байтов {bytes_num}')
        print(f'1 символ кодируется {bytes_num//len(arg)} байт\n')


if __name__ == '__main__':
    to_bytes('class', 'function', 'method')