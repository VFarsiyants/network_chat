class NoMesage(Exception):
    def __str__(self):
        return 'Нет сообщения от сервера'