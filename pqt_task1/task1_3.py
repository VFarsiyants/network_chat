"""
3. Написать функцию host_range_ping_tab(), возможности которой
основаны на функции из примера 2. Но в данном случае результат
должен быть итоговым по всем ip-адресам, представленным в 
табличном формате (использовать модуль tabulate). Таблица 
должна состоять из двух колонок и выглядеть примерно так:


Reachable
10.0.0.1
10.0.0.2
Unreachable
10.0.0.3
10.0.0.4
"""

from tabulate import tabulate
import ipaddress
import locale
import platform
from subprocess import Popen, PIPE
from threading import Thread
from itertools import zip_longest

ENCODING = locale.getpreferredencoding()


def ping_ip(ip_address, host_name=''):
    if 'available' not in globals().keys() or \
        'unavailable' not in globals().keys():
        raise TypeError('Списки available и unavailable должны быть определена в глобальной области видимости')
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    args = ['ping' , param, '4', str(ip_address)]
    reply = Popen(args, stdout=PIPE, stderr=PIPE)
    code = reply.wait()
    if code == 0:
        available.append(str(ip_address))
    else:
        unavailable.append(str(ip_address))


def host_range_ping(ip1, ip2):
    global available
    global unavailable
    available = []
    unavailable = []
    threads_list = []
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
        threads_list.append(thr)
        thr.start()
        ip_add1 += 1
    for thr in threads_list:
        thr.join()
    collumns = ['Reachable', 'Unreachable']
    data = []
    for ip_r, ip_unr in zip_longest(available, unavailable, fillvalue=''):
        data += [(ip_r, ip_unr)]
    print(tabulate(data, headers=collumns))


if __name__ == '__main__':
    host_range_ping('192.168.0.1', '192.168.0.255')