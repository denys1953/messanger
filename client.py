import pickle
import socket
import threading
import time
from datetime import datetime
import tkinter
from PIL import Image, ImageTk
import io
from customtkinter import *
from config import *


class Window:  # клас вікна в tkinter
    def __init__(self, type, srv):
        self.srv = srv
        self.thread = None
        self.type = type
        self.username = ""
        self.users_arr = None
        self.messages_arr = None
        self.active_users_arr = None
        self.img = Image.open("images/status.png")
        self.app = CTk(fg_color="#2C2C34")
        self.frame = CTkScrollableFrame(master=self.app, height=415, width=505, fg_color="#2C2C34")
        self.frame_nickname = CTkFrame(master=self.app, height=40, width=752, fg_color="#34333B", corner_radius=0)
        self.frame_users = CTkScrollableFrame(master=self.app, height=500, width=200, fg_color="#3B3A42",
                                              corner_radius=0)
        self.frame_nickname_status = CTkLabel(master=self.app, text='', fg_color="#34333B", font=("Calibri", 17),
                                              image=CTkImage(dark_image=self.img, light_image=self.img, size=(10, 10)))
        self.input = CTkEntry(master=self.app, placeholder_text="Написати повідомлення...", width=430)
        self.frame_nickname_label = CTkLabel(master=self.app, text_color="white", text=self.srv.user_to,
                                             fg_color="#34333B", font=("Calibri", 17))
        self.button = CTkButton(master=self.app, text="➤", font=("Helvetica", 20), width=15,
                                command=self.send_message_from_input, fg_color="#B18FCF", hover_color="#A48CB3")
        self.entry_login = CTkEntry(master=self.app, placeholder_text="Логін", width=250)
        self.entry_password = CTkEntry(master=self.app, placeholder_text="Пароль", width=250)
        self.button_login = CTkButton(master=self.app, text="Зареєструватись", width=100, command=self.register,
                                      fg_color="#B18FCF", hover_color="#A48CB3")
        self.button_register = CTkButton(master=self.app, text="Увійти", width=112, command=self.login,
                                         fg_color="#B18FCF", hover_color="#A48CB3")
        self.result_reg = CTkLabel(master=self.app, text="Користувач з таким ім'ям вже зареєстрований")
        self.result_log = CTkLabel(master=self.app, text="Невірний логін або пароль")

        self.app.geometry("500x400")
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
        set_appearance_mode("dark")
        set_default_color_theme("dark-blue")

    def draw_register_window(self):  # промальовує реєстраційне вікно
        self.entry_login.place(relx=0.5, rely=0.4, anchor="center")
        self.entry_password.place(relx=0.5, rely=0.5, anchor="center")
        self.button_login.place(relx=0.371, rely=0.6, anchor="center")
        self.button_register.place(relx=0.635, rely=0.6, anchor="center")

        self.srv.temp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.temp_client.connect(self.srv.ADDR)
        self.srv.thread = threading.Thread(target=self.srv.handle_client, daemon=True)
        self.srv.thread.start()
        self.srv.thread_count += 1

    def draw_window(self):  # промальовує основне вікно програми
        self.get_active_clients("", 4)

        self.app.geometry("750x500")
        self.frame_nickname_label = CTkLabel(master=self.app, text=self.srv.user_to, fg_color="#34333B",
                                             font=("Calibri", 17))
        self.frame_nickname.place(relx=0.28, rely=0)
        self.frame_users.place(relx=0, rely=0)
        self.frame_nickname_label.place(relx=0.3, rely=0.04, anchor="w")
        if self.srv.user_to in self.active_users_arr:
            self.frame_nickname_status.place(relx=0.3 + (len(self.srv.user_to) * 10) / 750, rely=0.042, anchor="w")
        self.frame.place(relx=0.29, rely=0.07)
        self.input.place(relx=0.36, rely=0.95, anchor="w")
        self.input.bind("<Return>", self.send_message_from_input)
        self.button.place(relx=0.94, rely=0.922)

        pin_img = CTkImage(dark_image=Image.open("images/skripka.png"), size=(20, 20))
        self.file_button = CTkButton(master=self.app, image=pin_img, text="", font=("Helvetica", 20), width=10,
                                     height=10, command=self.send_photo, fg_color="#B18FCF", hover_color="#A48CB3")

        self.file_button.place(relx=0.3, rely=0.922)

        result_users = self.get_users_from_database("users", 1)
        # print(result_users)

        # забирає і висвічує у вікні всіх користувачів
        for i in result_users:
            if i[1] != self.username:
                button_text = i[1]
                if button_text in self.active_users_arr:
                    img = CTkImage(dark_image=Image.open("images/status.png"), size=(10, 10))
                    but = CTkButton(master=self.frame_users, text=button_text, image=img, compound="right", width=215,
                                    height=40,
                                    command=lambda text=button_text: self.change_user(text),
                                    hover_color="#34333B",
                                    border_width=0.5, border_color="#34333B", corner_radius=0, text_color="white",
                                    font=("Calibri", 16))
                else:
                    but = CTkButton(master=self.frame_users, text=button_text, compound="right", width=215,
                                    height=40,
                                    command=lambda text=button_text: self.change_user(text),
                                    hover_color="#34333B",
                                    border_width=0.5, border_color="#34333B", corner_radius=0, text_color="white",
                                    font=("Calibri", 16))
                but.pack()
                if i[1] == self.srv.user_to:
                    but.configure(state="disabled", fg_color="#34333B")
                else:
                    but.configure(fg_color="#3B3A42")

        result_messages = self.get_users_from_database("messages", 1)
        # print(result_messages)

        # забирає і висвічує у вікні потрібні повідомлення користувачів
        for i in result_messages:
            if (self.username == i[1] and self.srv.user_to == i[2]) or (
                    self.username == i[2] and self.srv.user_to == i[1]):
                if i[4] == "":
                    received_message_label = CTkLabel(master=self.frame, text=i[3], text_color="white",
                                                      font=("Calibri", 16), wraplength=400, anchor="w")
                    received_message_label.pack(anchor="w", expand=True)
                else:
                    img = Image.open(io.BytesIO(i[4]))

                    tk_image = ImageTk.PhotoImage(img)
                    received_message_label = CTkLabel(master=self.frame, text_color="white", text=i[3],
                                                      font=("Calibri", 16),
                                                      wraplength=400, anchor="w")
                    received_message_label.pack(anchor="w", expand=True)
                    received_message_image = CTkLabel(master=self.frame, text_color="white", image=tk_image, text="",
                                                      font=("Calibri", 16),
                                                      wraplength=400, anchor="w")
                    received_message_image.pack(anchor="w", expand=True)

    def on_closing(self):  # перехоплює закривання вікна і закриває потік
        message = f"WM_DELETE_WINDOW {self.username}".encode(self.srv.FORMAT)
        self.app.grab_release()
        self.app.destroy()
        self.srv.temp_client.send(message)
        self.srv.connected = False
        # self.srv.thread.join()
        # self.srv.client.close()

    def send_photo(self):  # метод для відправки фотографій
        photo = filedialog.askopenfilename()
        photo_splitted = photo.split(".")
        format_n = ""

        if SERVER == "80.85.142.137":
            return

        if photo_splitted[-1] == "png":
            format = "PNG"
            format_n = "png"
        elif photo_splitted[-1] == "jpg":
            format = "JPEG"
            format_n = "jpg"
        else:
            return

        if photo:
            # self.compress_image(photo, f"images/photo.{format_n}", 200000)
            new_width = 750

            img = Image.open(photo)
            new_height = int(img.size[1] * (new_width / img.size[0]))
            img = img.resize((new_width, new_height))
            img.save(f"images/temp_photo.{format_n}")

            while os.path.getsize(f"images/temp_photo.{format_n}") > 25 * 1024:
                img = Image.open(photo)
                new_height = int(img.size[1] * (new_width / img.size[0]))
                img = img.resize((new_width, new_height))
                img.save(f"images/temp_photo.{format_n}")
                new_width -= 50

            img_bytes = io.BytesIO()
            img.save(img_bytes, format=format)
            img_bytes = img_bytes.getvalue()

            message = f"| {str(datetime.now())[:19]} |  {self.username}:    :.,;".encode()

            self.send_message_from_input(is_image=True, image=img)
            self.srv.connect(self.username, self.srv.user_to, 5, "messages", message + img_bytes)

    def change_user(self, username):  # зміна користувача, якому ми хочемо написати
        self.srv.user_to = username
        self.clear_register_window()

    def clear_register_window(self):  # очищає реєстраційне вікно для подальшої промальовки основного вікна
        self.entry_login.place_forget()
        self.entry_password.place_forget()
        self.button_login.place_forget()
        self.button_register.place_forget()
        self.result_reg.place_forget()
        self.result_log.place_forget()
        self.frame_nickname.place_forget()
        children_buttons = self.frame_users.winfo_children()
        # Проходження по кожному дочірньому віджету і видалення його
        for child in children_buttons:
            child.destroy()

        children_messages = self.frame.winfo_children()
        for child in children_messages:
            child.destroy()
        self.frame_nickname_label.place_forget()
        self.frame_nickname_status.place_forget()
        self.draw_window()

    def get_users_from_database(self, table, type_n, login="1", password="1", msg=""):  # відправляє повідомлення на сервер з поміткою щоб получити массив користувачів або повідомлень
        self.srv.connect(login, password, type_n, table, msg)

        if table == "users":
            while self.users_arr == None:
                pass
            return self.users_arr
        elif table == "messages":
            while self.messages_arr == None:
                pass
            return self.messages_arr

    def get_active_clients(self, table, type_n, login="1", password="1", msg=""):  # повертає масив користувачів, які є в мережі
        self.srv.connect(login, password, type_n, table, msg)

        while self.active_users_arr == None:
            pass

    def add_user(self, login, password, type_n, table, msg=""):  # відправляє на сервер повідомлення для додавання користувача в бд
        self.srv.connect(login, password, type_n, table, msg)

    def add_message(self, username, user_to, type_n, table, msg):  # відправляє на сервер повідомлення для додавання повідомлення в бд
        self.srv.connect(username, user_to, type_n, table, msg)

    def register(self):  # метод для реєстрації користувача
        login = self.entry_login.get()
        password = self.entry_password.get()
        self.result_log.configure(text="Невірний логін або пароль")

        if login == "" or password == "":
            self.result_log.configure(text="Недопустиме значення в полях вводу")
            self.result_log.place(relx=0.5, rely=0.3, anchor="center")
            return


        for i in self.get_users_from_database("users", 1, login, password):
            if login == i[1]:
                self.result_reg.place(relx=0.5, rely=0.3, anchor="center")
                return

        self.add_user(login, password, 2, "users")
        self.username = login
        self.app.title(login)
        self.clear_register_window()

    def login(self):  # метод для авторизації користувача
        login = self.entry_login.get()
        self.username = login
        password = self.entry_password.get()

        for i in self.get_users_from_database("users", 1, login, password):
            if login == i[1] and password == i[2]:
                self.get_active_clients("", 4)
                if self.srv.error_message == "Користувач з таким ім'ям зараз авторизований":
                    self.result_log.configure(text="Користувач з таким ім'ям зараз авторизований")
                    self.result_log.place(relx=0.5, rely=0.3, anchor="center")
                    self.srv.error_message = None
                    return
                if login == "denys":
                    self.srv.user_to = "Стас"
                self.clear_register_window()
                self.app.title(login)
                return

        self.result_log.place(relx=0.5, rely=0.3, anchor="center")
        self.entry_login.delete(0, tkinter.END)
        self.entry_password.delete(0, tkinter.END)
        return

    def send_message_from_input(self, event=None, is_image=False, image=None):  # метод для відправки повідомлення іншому користувачу і в бд
        if is_image == False:
            message = self.input.get()
            if len(message) == 0:
                return
            self.input.delete(0, tkinter.END)
            message = f"| {str(datetime.now())[:19]} |  {self.username}:    " + message

            self.add_message(self.username, self.srv.user_to, 3, "messages", message)
            self.srv.send_message(f"{self.srv.user_to};,." + message)

            sent_message_label = CTkLabel(master=self.frame, text_color="white", text=message, font=("Calibri", 16),
                                          wraplength=400, anchor="w")
            sent_message_label.pack(anchor="w", expand=True)
        else:

            tk_image = ImageTk.PhotoImage(image)

            message = f"| {str(datetime.now())[:19]} |  {self.username}:    "
            sent_message_label = CTkLabel(master=self.frame, text_color="white", text=message, font=("Calibri", 16),
                                          wraplength=400, anchor="w")
            sent_message_label.pack(anchor="w", expand=True)
            sent_message_label = CTkLabel(master=self.frame, text_color="white", image=tk_image, text="",
                                          font=("Calibri", 16),
                                          wraplength=400, anchor="w")
            sent_message_label.pack(anchor="w", expand=True)

    def update_label(self, message, type):  # промальовує нове повідомлення у вікні
        if type == "text":
            received_message_label = CTkLabel(master=self.frame, text_color="white", text=message, font=("Calibri", 16),
                                              wraplength=400, anchor="w")
            received_message_label.pack(anchor="w", expand=True)
        elif type == "image":
            img = Image.open(io.BytesIO(message.split(b":.,;")[1]))

            tk_image = ImageTk.PhotoImage(img)
            received_message_label = CTkLabel(master=self.frame, text_color="white",
                                              text=message.split(b":.,;")[0].decode(),
                                              font=("Calibri", 16),
                                              wraplength=400, anchor="w")
            received_message_label.pack(anchor="w", expand=True)
            received_message_image = CTkLabel(master=self.frame, text_color="white", image=tk_image, text="",
                                              font=("Calibri", 16),
                                              wraplength=400, anchor="w")
            received_message_image.pack(anchor="w", expand=True)

    def loop(self):  # робить так щоб вікно не закривалось саме після запуску
        self.app.mainloop()


class Client:
    def __init__(self, host, port):
        self.wnd = None
        self.FORMAT = 'utf-8'
        self.SERVER = host
        self.PORT = port
        self.thread = None
        self.connected = True
        self.thread_count = 0
        self.username = ""
        self.user_to = "denys"
        self.DISCONECT_MESSAGE = '!DISCONNECT'
        self.ADDR = (host, port)
        self.error_message = None
        self.temp_client = None

    def connect(self, login, password, type_n, table, msg):  # багатофункціональний метод, в залежності від аргументу type_n робить різні дії
        if type_n == 5:
            message = f"temp_connect:.,;{login}:.,;{password}:.,;{type_n}:.,;{table}:.,;".encode() + msg
        else:
            time.sleep(0.1)
            message = f"temp_connect:.,;{login}:.,;{password}:.,;{type_n}:.,;{table}:.,;{msg}".encode(
                self.FORMAT)
        self.temp_client.send(message)

    def send_message(self, msg=""):  # відправка повідомлення на сервер
        message = msg.encode(self.FORMAT)
        self.temp_client.send(message)

    def handle_client(self):  # перехоплення повідомлення від серверу
        while self.connected:
            msg = self.temp_client.recv(10000000)

            msg_splitted = msg.split(b":,")

            if msg_splitted[0] == b"GET_USERS":
                self.wnd.users_arr = pickle.loads(msg_splitted[1])
                continue
            elif msg_splitted[0] == b"GET_MESSAGES":
                self.wnd.messages_arr = pickle.loads(msg_splitted[1])
                continue
            elif msg_splitted[0] == b"GET_ACTIVE_USERS":
                self.wnd.active_users_arr = pickle.loads(msg_splitted[1])
                continue
            elif msg_splitted[0] == b"CONNECTION_ERROR":
                self.error_message = "Користувач з таким ім'ям зараз авторизований"
                continue
            if len(msg) < 1000:
                self.wnd.update_label(msg.decode(), "text")
            else:
                self.wnd.update_label(msg, "image")


cl = Client(SERVER, 5000)


def run_tkinter_in_thread():  # запуск вікна
    window = Window("Client", cl)

    cl.wnd = window

    window.draw_register_window()
    window.loop()


tkinter_thread = threading.Thread(target=run_tkinter_in_thread)
tkinter_thread.start()

