import pickle
import socket
import sqlite3
import threading


class Database: # клас бази даних
    def __init__(self, src):
        self.conn = sqlite3.connect(src)
        self.cur = self.conn.cursor()

    def create_base_table(self): # метод, для створення таблиць, якщо вони не існують
        self.cur.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        nickname TEXT NOT NULL,
                        password TEXT NOT NULL)''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY,
                        message_from TEXT NOT NULL,
                        message_to TEXT NOT NULL,
                        content TEXT,
                        image BLOG)
                        ''')

    def add_user(self, login, password):  # додавання користувача
        print(login, password)
        self.cur.execute("INSERT INTO users (nickname, password) VALUES (?, ?)", (login, password))
        self.conn.commit()

    def add_message(self, message_from, message_to, content, image):  # додавання повідомлення
        self.cur.execute("INSERT INTO messages (message_from, message_to, content, image) VALUES (?, ?, ?, ?)",
                         (message_from, message_to, content, image))
        self.conn.commit()

    def get_all_users(self, table): # повертає масив користувачів або повідомлень (залежно від аргументу)
        self.cur.execute(f"SELECT * FROM {table}")
        result = self.cur.fetchall()

        return result


class Server:
    def __init__(self, host, port, db_src=None):
        self.db_src = db_src
        self.FORMAT = 'utf-8'
        self.SERVER = host
        self.PORT = port
        self.DISCONECT_MESSAGE = '!DISCONNECT'
        self.client = [0]
        self.clients = {}
        self.temp_msg = None
        self.ADDR = (host, port)
        self.server = None

    def connect(self): # підключає server до ip адреси і порта
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(self.ADDR)

    def send_message(self, msg_to, msg="", type=""):  # відправка повідомлення на сервер
        if type == "image":
            message = msg
        else:
            message = msg.encode(self.FORMAT)
            # self.client[0].send(message)
            print(msg_to)

        for addr, conn in self.clients.items():
            if addr == msg_to:
                print(message)
                conn.send(message)

    def check_online(self, user):  # перевірка чи вибраний користувач в мережі
        for i in self.clients.items():
            if i[0] == user:
                return True
        return False

    def handle_client(self, conn, addr):  # перехоплює повідомлення від клієнта
        connected = True
        while connected:
            try:
                db = Database(self.db_src)

                msg = conn.recv(10000000)
                print(msg)
                if len(msg) > 1000:
                    msg_splitted_temp = msg.split(b":.,;")
                    login, user_to, type_n, table, msg, image = msg_splitted_temp[1].decode(), msg_splitted_temp[
                        2].decode(), msg_splitted_temp[3].decode(), msg_splitted_temp[4].decode(), msg_splitted_temp[
                        5].decode(), msg_splitted_temp[6]
                    db.add_message(login, user_to, msg, sqlite3.Binary(image))

                    if self.check_online(user_to):
                        self.send_message(user_to, msg.encode() + b":.,;" + image, "image")
                    continue
                msg = msg.decode(self.FORMAT)
                msg_splitted_temp = msg.split(":.,;")
                # if len(msg_splitted_temp) > 5:
                #     msg_splitted_temp = msg_splitted_temp[5:]
                msg_splitted = msg.split(" ")
                if msg_splitted_temp[0] == "temp_connect":
                    login, password, type_n, table, msg = msg_splitted_temp[1], msg_splitted_temp[2], msg_splitted_temp[
                        3], msg_splitted_temp[4], msg_splitted_temp[5]

                    type_n = str(type_n)

                    print(msg_splitted_temp)

                    if login != "1":
                        if login in list(self.clients.keys()):
                            conn.send("CONNECTION_ERROR".encode())
                        else:
                            self.clients[login] = conn
                    else:
                        self.clients[login] = conn

                    if type_n == "1":
                        print(table, "111111")
                        if table == "users":
                            msg_db_result = f"GET_USERS:,".encode() + pickle.dumps(db.get_all_users('users'))
                        elif table == "messages":
                            print("hhhh")
                            msg_db_result = f"GET_MESSAGES:,".encode() + pickle.dumps(db.get_all_users('messages'))
                            print(msg_db_result)
                        conn.send(msg_db_result)
                    elif type_n == "2":
                        db.add_user(login, password)
                    elif type_n == "3":
                        db.add_message(login, password, msg, "")
                    elif type_n == "4":
                        conn.send(f"GET_ACTIVE_USERS:,".encode() + pickle.dumps(list(self.clients.keys())))
                    elif type_n == "5":
                        pass
                    continue

                if msg_splitted[0] == "Підключення":
                    # if msg_splitted[1] in self.clients.keys()
                    self.clients[msg_splitted[1]] = conn
                    print(F"[НОВЕ ПІДКЛЮЧЕННЯ] {msg_splitted[1]} підключено.")
                    continue

                if msg_splitted[0] == "WM_DELETE_WINDOW":
                    del self.clients[msg_splitted[1]]
                    print(f"[ВІДКЛЮЧЕННЯ] було відключено користувача {msg_splitted[1]}")
                    print(f"[АКТИВНІ ПІДКЛЮЧЕННЯ] {threading.activeCount() - 2}")
                    continue

                if msg == self.DISCONECT_MESSAGE:
                    connected = False

                print(f"[{addr}] {msg.split(';,.')[1]}")
                if self.check_online(msg.split(';,.')[0]):
                    self.send_message(msg.split(';,.')[0], msg.split(';,.')[1])
            except Exception as ex:
                print(ex)
                import traceback
                traceback.print_exc()
                print(f"З'єднання з {addr} було неналежно закрито.")
                connected = False
                continue

        conn.close()

    def start(self):  # початок виконання server.py
        self.connect()
        self.server.listen()
        print(f"[ОЧІКУВАННЯ] сервер очікує підключення {self.SERVER}")
        while True:
            conn, addr = self.server.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.start()
            print(f"[АКТИВНІ ПІДКЛЮЧЕННЯ] {threading.activeCount() - 2}")
