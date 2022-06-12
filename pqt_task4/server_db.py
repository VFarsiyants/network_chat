from pprint import pprint

from sqlalchemy import create_engine, Table, MetaData, Column, \
    Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker
from datetime import datetime


class ServerStorage:
    # Экземпляр класса == запись в таблице
    # Пользователь
    class User:
        def __init__(self, username):
            self.name = username
            self.last_login = datetime.now()
            self.id = None

    # Активный пользователь
    class ActiveUser:
        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    # История входов =
    class LoginHistory:
        def __init__(self, user_id, date, ip_address, port):
            self.id = None
            self.user = user_id
            self.date = date
            self.ip_address = ip_address
            self.port = port

    # Класс - отображение таблицы контактов пользователей
    class UserContact:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    # Класс отображение таблицы истории действий
    class UserHistory:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        # SERVER_DATABASE - sqlite:///server_base.db3
        self.database_engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

        self.metadata = MetaData()

        # таблицы

        # Пользователи
        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime)
                            )

        # Активные пользователи
        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'), unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime)
                                   )

        # История входов
        user_login_history = Table('Login_history', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id')),
                                   Column('date', DateTime),
                                   Column('ip_address', String),
                                   Column('port', String)
                                   )

        # Создаём таблицу контактов пользователей
        contacts = Table('Contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user', ForeignKey('Users.id')),
                         Column('contact', ForeignKey('Users.id'))
                         )

        # Создаём таблицу истории пользователей
        user_history_table = Table('History', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id')),
                                   Column('sent', Integer),
                                   Column('accepted', Integer)
                                   )

        self.metadata.create_all(self.database_engine)

        # Связываем классы с таблицей
        mapper(self.User, users_table)
        mapper(self.ActiveUser, active_users_table)
        mapper(self.LoginHistory, user_login_history)
        mapper(self.UserContact, contacts)
        mapper(self.UserHistory, user_history_table)

        # Создание сессии
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # Когда устанавливаем соединение, очищаем таблицу активных пользователей
        self.session.query(self.ActiveUser).delete()
        self.session.commit()

    def user_login(self, username, ip_address, port):
        """
        Добавления пользователя в список пользователей (если необходимо)
        Обновление информации по последнему входу в чат
        """
        rez = self.session.query(self.User).filter_by(name=username)
        if rez.count():
            user = rez.first()
            user.last_login = datetime.now()
        else:
            user = self.User(username)
            self.session.add(user)
            self.session.commit()
            user_in_history = self.UserHistory(user.id)
            self.session.add(user_in_history)

        new_active_user = self.ActiveUser(user.id, ip_address, port, datetime.now())
        self.session.add(new_active_user)

        history = self.LoginHistory(user.id, datetime.now(), ip_address, port)
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        """
        Выход пользователя из чата
        """
        user = self.session.query(self.User).filter_by(name=username).first()
        self.session.query(self.ActiveUser).filter_by(user=user.id).delete()
        self.session.commit()

    # Функция фиксирует передачу сообщения и делает соответствующие отметки в БД
    def process_message(self, sender, recipient):
        # Получаем ID отправителя и получателя
        sender = self.session.query(self.User).filter_by(name=sender).first().id
        recipient = self.session.query(self.User).filter_by(name=recipient).first().id
        # Запрашиваем строки из истории и увеличиваем счётчики
        sender_row = self.session.query(self.UserHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UserHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    # Функция добавляет контакт для пользователя.
    def add_contact(self, user, contact):
        # Получаем ID пользователей
        user = self.session.query(self.User).filter_by(name=user).first()
        contact = self.session.query(self.User).filter_by(name=contact).first()

        # Проверяем что не дубль и что контакт может существовать (полю пользователь мы доверяем)
        if not contact or self.session.query(self.UserContact).filter_by(user=user.id,
                                                                         contact=contact.id).count():
            return

        # Создаём объект и заносим его в базу
        contact_row = self.UserContact(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    # Функция удаляет контакт из базы данных
    def remove_contact(self, user, contact):
        # Получаем ID пользователей
        user = self.session.query(self.User).filter_by(name=user).first()
        contact = self.session.query(self.User).filter_by(name=contact).first()

        # Проверяем что контакт может существовать (полю пользователь мы доверяем)
        if not contact:
            return

        # Удаляем требуемое
        print(self.session.query(self.UserContact).filter(
            self.UserContact.user == user.id,
            self.UserContact.contact == contact.id
        ).delete())
        self.session.commit()

    def users_list(self):
        """
        Список всех пользователей
        """
        query = self.session.query(
            self.User.name,
            self.User.last_login
        )
        return query.all()

    def active_users_list(self):
        """
        Список активных пользователей
        """
        query = self.session.query(
            self.User.name,
            self.ActiveUser.ip_address,
            self.ActiveUser.port,
            self.ActiveUser.login_time
        ).join(self.User)
        return query.all()

    def login_history(self, username=None):
        """
        История логина пользователей
        """
        query = self.session.query(self.User.name,
                                   self.LoginHistory.date,
                                   self.LoginHistory.ip_address,
                                   self.LoginHistory.port
                                   ).join(self.User)
        if username:
            query = query.filter(self.User.name == username)
        return query.all()

    # Функция возвращает список контактов пользователя.
    def get_contacts(self, username):
        # Запрашиваем указанного пользователя
        user = self.session.query(self.User).filter_by(name=username).one()

        # Запрашиваем его список контактов
        query = self.session.query(self.UserContact, self.User.name). \
            filter_by(user=user.id). \
            join(self.User, self.UserContact.contact == self.User.id)

        # выбираем только имена пользователей и возвращаем их.
        return [contact[1] for contact in query.all()]

    # Функция возвращает количество переданных и полученных сообщений
    def message_history(self):
        query = self.session.query(
            self.User.name,
            self.User.last_login,
            self.UserHistory.sent,
            self.UserHistory.accepted
        ).join(self.User)
        # Возвращаем список кортежей
        return query.all()


"""Блок отладки"""
if __name__ == '__main__':
    test_db = ServerStorage('server_base.db3')
    test_db.user_login('1111', '192.168.1.113', 8080)
    test_db.user_login('McG2', '192.168.1.113', 8081)
    pprint(test_db.users_list())
    pprint(test_db.active_users_list())
    test_db.user_logout('McG2')
    pprint(test_db.login_history('re'))
    test_db.add_contact('test2', 'test1')
    test_db.add_contact('test1', 'test3')
    test_db.add_contact('test1', 'test6')
    test_db.remove_contact('test1', 'test3')
    test_db.process_message('McG2', '1111')
    pprint(test_db.message_history())
