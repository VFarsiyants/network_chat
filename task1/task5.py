"""
5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать результаты из байтовового в строковый тип на кириллице.
"""

from email.policy import default
import locale
import subprocess
import platform


def ping(resource):
    default_encoding = locale.getpreferredencoding()
    print('*'*80)
    print(f'Пингуем ресурс {resource}')
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    args = ['ping', param, '2', resource]
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    for line in process.stdout:
        line = line.decode(default_encoding)
        print(line)


if __name__ == '__main__':
    ping('yandex.ru')
    ping('youtube.com')
