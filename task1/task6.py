"""
6. Создать текстовый файл test_file.txt, заполнить его тремя строками: 
«сетевое программирование», «сокет», «декоратор». Проверить кодировку файла 
по умолчанию. Принудительно открыть файл в формате Unicode и вывести его 
содержимое.
"""

from chardet import detect


def create_file(name, lines):
    print('\nСоздаем файл\n')
    f = open(name, 'wb')
    for line in lines:
        f.write((line + '\n').encode('utf-8'))
    f.close()


def read_file(name):
    print('\nЧитаем файл\n')
    with open(name, 'rb') as f:
        content = f.read()
    encoding = detect(content)['encoding']
    print(f'Кодировка файла {encoding}')
    print('\nСодержимое файла:\n')
    print(content.decode(encoding))

if __name__ == '__main__':
    lines = ['сетевое программирование', 'сокет', 'декоратор']
    file_name = 'test_file.txt'
    create_file(file_name, lines)
    print('Мы забыли про файл')
    read_file(file_name)
