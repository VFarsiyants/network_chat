"""
4. Преобразовать слова «разработка», «администрирование», «protocol», 
«standard» из строкового представления в байтовое и выполнить обратное 
преобразование (используя методы encode и decode).
"""


def task(*args):
    for arg in args:
        print('\n')
        print('*' * 80)
        print(f'Работаем со словом {arg}')
        arg_encoded = arg.encode('utf-8')
        print(f'В байтвоом представлении\n{arg_encoded}')
        print('Обратное преобразование к строке')
        arg_str = arg_encoded.decode('utf-8')
        print(arg_str)


if __name__ == '__main__':
    words = ['разработка', 'администрирование', 'protocol']
    task(*words)
