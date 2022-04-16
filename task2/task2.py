"""
2. Задание на закрепление знаний по модулю json. Есть файл orders в формате 
JSON с информацией о заказах. Написать скрипт, автоматизирующий его заполнение 
данными. Для этого:

Создать функцию write_order_to_json(), в которую передается 5 параметров — 
товар (item), количество (quantity), цена (price), покупатель (buyer), дата 
(date). Функция должна предусматривать запись данных в виде словаря в файл 
orders.json. При записи данных указать величину отступа в 4 пробельных символа;
Проверить работу программы через вызов функции write_order_to_json() с 
передачей в нее значений каждого параметра
"""
import json
import os


def write_order_to_json(item, quantity, price, buyer, date):
    filename = [file for file in os.listdir() if file.endswith('.json')][0]
    with open(filename, 'r+') as f:
        orders = json.load(f)
        f.seek(0)
        orders['orders'] += [{'item': item, 'quantity': quantity,
                              'price': price, 'buyer': buyer, 'date': date}]
        json.dump(orders, f, indent=4)


if __name__ == '__main__':
    write_order_to_json('Носки', 4, 299, 'Мороженщик', '16.04.2022')
    write_order_to_json('Трусы', 10, 2999, 'Менеджер', '10.04.2022')
