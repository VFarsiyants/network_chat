"""1. Написать функцию host_ping(), в которой с помощью утилиты ping 
будет проверяться доступность сетевых узлов. Аргументом функции 
является список, в котором каждый сетевой узел должен быть 
представлен именем хоста или ip-адресом. В функции необходимо 
перебирать ip-адреса и проверять их доступность с выводом 
соответствующего сообщения («Узел доступен», «Узел недоступен»). При 
этом ip-адрес сетевого узла должен создаваться с помощью функции 
ip_address(). (Внимание! Аргументом сабпроцеса должен быть список, а 
не строка!!! Для уменьшения времени работы скрипта при проверке 
нескольких ip-адресов, решение необходимо выполнить с помощью потоков)"""
import ipaddress
import socket
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

def ping_ips(ip_list):
    for ip in ip_list:
        ip_adr = None
        try:
            ip_adr = ipaddress.ip_address(ip)
            host_name = ''
        except ValueError:
            try:
                ip_adr = ipaddress.ip_address(socket.gethostbyname(ip))
                host_name = ip
            except:
                print(f'Ошибка при получении IP для "{ip}"')
        if not ip_adr:
            continue
        thr = Thread(target=ping_ip, args=(ip_adr, host_name, ))
        thr.start()

if __name__ == '__main__':
    ip_list = ['a', 'google.com', 'yandex.ru', '192.168.1.1']
    ping_ips(ip_list=ip_list)
