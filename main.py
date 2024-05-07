import threading
from server import Server, Database
from config import *

srv = Server(SERVER, 5000, "database.db")
db = Database("database.db")
db.create_base_table()

srv.db = db

print("[ЗАПУСК] сервер запускається...")

server_thread = threading.Thread(target=srv.start)
server_thread.start()
