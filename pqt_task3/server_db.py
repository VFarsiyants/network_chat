from datetime import datetime
from sqlalchemy import create_engine, Table, MetaData, Column, \
    Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker
from common.variables import SERVER_DATABASE


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

    def __init__(self):
        # SERVER_DATABASE - sqlite:///server_base.db3
        self.database_engine = create_engine(SERVER_DATABASE, echo=False, pool_recycle=7200)

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

        self.metadata.create_all(self.database_engine)

        # Связываем классы с таблицей
        mapper(self.User, users_table)
        mapper(self.ActiveUser, active_users_table)
        mapper(self.LoginHistory, user_login_history)


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
        print(username, ip_address, port)
        rez = self.session.query(self.User).filter_by(name=username)
        if rez.count():
            user = rez.first()
            user.last_login = datetime.now()
        else:
            user = self.User(username)
            self.session.add(user)
            self.session.commit()

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


"""Блок отладки"""
if __name__ == '__main__':
    test_db = ServerStorage()
    test_db.user_login('client_1', '192.168.1.4', 8080)
    test_db.user_login('client_2', '192.168.1.5', 7777)
    print(' ---- test_db.active_users_list() ----')
    print(test_db.active_users_list())
    test_db.user_logout('client_1')
    print(' ---- test_db.active_users_list() after logout client_1 ----')
    print(test_db.active_users_list())
    print(' ---- test_db.login_history(client_1) ----')
    print(test_db.login_history('client_1'))
    print(' ---- test_db.users_list() ----')
    print(test_db.users_list())
