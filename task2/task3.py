"""
3. Задание на закрепление знаний по модулю yaml. Написать скрипт, 
автоматизирующий сохранение данных в файле YAML-формата. Для этого:

Подготовить данные для записи в виде словаря, в котором первому ключу 
соответствует список, второму — целое число, третьему — вложенный словарь, 
где значение каждого ключа — это целое число с юникод-символом, отсутствующим 
в кодировке ASCII (например, €);
Реализовать сохранение данных в файл формата YAML — например, в файл file.yaml. 
При этом обеспечить стилизацию файла с помощью параметра default_flow_style, 
а также установить возможность работы с юникодом: allow_unicode = True;
Реализовать считывание данных из созданного файла и проверить, совпадают ли они 
с исходными.
"""
import yaml


data_to_yaml = {
    '1': [1, 'rick', 'огурчик'],
    '2': 2542,
    '3': {
        '1': '€',
        '2': '₽'
    }
}

with open('data_write.yaml', 'w') as f:
    yaml.dump(data_to_yaml, f, default_flow_style=False, allow_unicode=True)

with open('data_write.yaml') as f:
    content = yaml.full_load(f)
    print('Данные файла yaml\n')
    print(content, '\n')
    print('Проверка соответсвия записанных и считанных данных',
          content == data_to_yaml)
