"""
3. Определить, какие из слов «attribute», «класс», «функция», «type» 
невозможно записать в байтовом типе.
"""

from task2 import to_bytes

if __name__ == '__main__':
    words = ['attribute', 'класс', 'функция', 'type']
    for word in words:
        to_bytes(word)
