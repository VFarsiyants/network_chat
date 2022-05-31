"""
2. Написать функцию host_range_ping() (возможности которой основаны на функции из примера 1) для перебора ip-адресов из заданного диапазона. Меняться должен только последний октет каждого адреса. По результатам проверки должно выводиться соответствующее сообщение.
"""
import ipaddress
import locale
import platform
from subprocess import Popen, PIPE
from threading import Thread

ENCODING = locale.getpreferredencoding()


def ping_ip(ip_address, host_name=''):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    args = ['ping' , param, '4', str(ip_address)]
    reply = Popen(args, stdout=PIPE, stderr=PIPE)
    code = reply.wait()
    if code == 0:
        print(f'{ip_address} ({host_name}) - Узел доступен')
    else:
        print(f'{ip_address} ({host_name}) - Узел недоступен')


def host_range_ping(ip1, ip2):
    try:
        ip_add1 = ipaddress.ip_address(ip1)
        ip_add2 = ipaddress.ip_address(ip2)
        if ip_add2 < ip_add1 or \
            str(ip_add1).split('.')[0:-1] != str(ip_add2).split('.')[0:-1]:
            raise ValueError
    except ValueError:
        print('Один из IP адресов указан неккорректно')
    ip_range = int(str(ip_add2).split('.')[-1]) - int(str(ip_add1).split('.')[-1])
    for _ in range(ip_range + 1):
        thr = Thread(target=ping_ip, args=(ip_add1, ))
        thr.start()
        ip_add1 += 1


if __name__ == '__main__':
    host_range_ping('192.168.0.1', '192.168.0.255')