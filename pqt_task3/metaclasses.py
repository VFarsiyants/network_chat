import dis
from pprint import pprint

class ClientValidation(type):
    # параметры при отработке метакласса:
    # имя, от чего наследуемся, словарь переменных
    def __init__(cls, clsname, bases, clsdict):
        calls = []
        for obj_key in clsdict:
            try:
                ret = dis.get_instructions(clsdict[obj_key])
                # метод возвращает инструкцию по функции
                # а если передана не фукнция то получаем 
                # исключение и переходим к следующей итерации
            except TypeError:
                pass
            else:
                # разбираем код функции
                for inst in ret:
                    if inst.opname == 'LOAD_GLOBAL':
                        if inst.argval not in calls:
                            calls.append(inst.argval)
        # вытянув вызываемые объекты проверяем если среди них 
        # есть недопустимые
        for call in ('accept', 'listen', 'socket'):
            if call in calls:
                raise TypeError(f'Вызов недопустимого метод в классе:\n{call}')
        # Хотя бы одна из функций работающая с сокетами должна 
        # вызываться в классе.
        if 'get_message' not in calls and 'send_message' not in calls:
            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами.')
        super().__init__(clsname, bases, clsdict)


class ServerValidator(type):
    def __init__(cls, clsname, bases, clsdict):
        global_calls = []
        method_calls = []
        attrs = []
        for obj_key in clsdict:
            try:
                ret = dis.get_instructions(clsdict[obj_key])
            except TypeError:
                pass
            else:
                for inst in ret:
                    print(inst)
                    if inst.opname == 'LOAD_GLOBAL':
                        if inst.argval not in global_calls:
                            global_calls += [inst.argval]
                    elif inst.opname == 'LOAD_METHOD':
                        if inst.argval not in method_calls:
                            method_calls += [inst.argval]
                    elif inst.opname == 'LOAD_ATTR':
                        if inst.argval not in attrs:
                            attrs += [inst.argval]
        print(20*'-', 'methods', 20*'-')
        pprint(global_calls)
        print(20*'-', 'methods_2', 20*'-')
        pprint(method_calls)
        print(20*'-', 'attrs', 20*'-')
        pprint(attrs)
        print(50*'-')
        if 'connect' in global_calls:
            raise TypeError('Использование метода connect недопустимо в серверном классе')
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета.')
        super().__init__(clsname, bases, clsdict)
