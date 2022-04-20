"""
1. Задание на закрепление знаний по модулю CSV. Написать скрипт, осуществляющий 
выборку определенных данных из файлов info_1.txt, info_2.txt, info_3.txt и 
формирующий новый «отчетный» файл в формате CSV. Для этого:

Создать функцию get_data(), в которой в цикле осуществляется перебор файлов с 
данными, их открытие и считывание данных. В этой функции из считанных данных 
необходимо с помощью регулярных выражений извлечь значения параметров 
«Изготовитель системы», «Название ОС», «Код продукта», «Тип системы». Значения 
каждого параметра поместить в соответствующий список. Должно получиться четыре 
списка — например, os_prod_list, os_name_list, os_code_list, os_type_list. 
В этой же функции создать главный список для хранения данных отчета — например, 
main_data — и поместить в него названия столбцов отчета в виде списка: 
«Изготовитель системы», «Название ОС», «Код продукта», «Тип системы». 
Значения для этих столбцов также оформить в виде списка и поместить в файл 
main_data (также для каждого файла);

Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл. 
В этой функции реализовать получение данных через вызов функции get_data(), 
а также сохранение подготовленных данных в соответствующий CSV-файл;
Проверить работу программы через вызов функции write_to_csv().
"""
import encodings
import re
import csv
import os
from chardet import detect


def get_data():
    main_data = [['Изготовитель системы',
                  'Название ОС', 'Код продукта', 'Тип системы']]
    for filename in ([filename for filename in os.listdir() if filename.endswith('.txt')]):
        with open(filename, 'rb') as f:
            content = f.read()
            encoding = detect(content)['encoding']
            content_dec = content.decode(encoding)
            main_data += [[]]
            for header in main_data[0]:
                data = (re.search(r'({}:)\s+(.+\w)'.format(header),
                        content_dec).group(2))
                main_data[-1] += [data]
    return main_data


def write_to_csv(filename):
    with open(filename, 'w') as f:
        f_writter = csv.writer(f)
        f_writter.writerows(get_data())


if __name__ == '__main__':
    write_to_csv('result.csv')
