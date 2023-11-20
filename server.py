import socket
import ssl
import threading
import mysql.connector
import json
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding,rsa
import hashlib

def reliable_send(ssl_client_socket,message):
    message = json.dumps(message)
    ssl_client_socket.send(message.encode('utf-8'))

def reliable_recv(ssl_client_socket):
    json_data = ""
    while True:
        try:
            json_data += ssl_client_socket.recv(1024).decode('utf-8')
            return json.loads(json_data)
        except ValueError:
            continue

def register(message):
    queary = f"SELECT * FROM users WHERE username = '{message[1]}'"
    cursor.execute(queary)
    rows = cursor.fetchall()
    if len(rows) == 0 or rows==None:
        queary = f"INSERT INTO users (username, password) VALUES ('{message[1]}', '{hashlib.md5(message[2].encode()).hexdigest()}')"
        cursor.execute(queary)
        db.commit()
        return "register successful"
    else:
        return "User already exists"

def login(message):
    queary = f"SELECT * FROM users WHERE username = '{message[1]}'"
    cursor.execute(queary)
    rows = cursor.fetchall()
    if len(rows) == 0 or rows==None:
        return "User not found"
    else:
        if rows[0][1] == hashlib.md5(message[2].encode()).hexdigest():
            online_users[message[1]] = ssl_client_socket
            global is_logged_in
            is_logged_in = True
            return "login successful"
        else:
            return "Incorrect password"

def request_public_key(message):
    if message[1] not in online_users:
        return "user is offline"
    else:
        queary = f"SELECT * FROM users WHERE username = '{message[1]}'"
        cursor.execute(queary)
        rows = cursor.fetchall()
        return rows[0][2]

def send_message(message, is_logged_in):
    if is_logged_in==True:
        if message[1] in online_users:
            ssl_client_socket = online_users[message[1]]
            message_to_send = f"send_message:{message[2]}"
            reliable_send(ssl_client_socket, message_to_send)
            return "Message sent"
        else:
            return "User is offline"
    else:
        return "Please login first"

def logout(message, is_logged_in):
    if is_logged_in==True:
        online_users.pop(message[1])
        return "logout successful"
    else:
        return "Please login first"

def update_public_key(message):
    queary=f"UPDATE users SET pub_key = '{message[2]}' , update_time = NOW() WHERE username = '{message[1]}'"
    cursor.execute(queary)
    db.commit()
    return "public key updated"

def handle_client(ssl_client_socket):
    is_logged_in = False
    while True:
        message = reliable_recv(ssl_client_socket)
        print(message)
        if message[0] == "register":
            message_result = register(message)
        elif message[0] == "login":
            message_result = login(message)
        elif message[0] == "update_public_key":
            message_result=update_public_key(message)
        elif message[0] == "request_public_key":
            message_result = request_public_key(message)
        elif message[0] == "send_message":
            message_result = send_message(message, is_logged_in)
        elif message[0] == "logout":
            message_result = logout(message, is_logged_in)
        else:
            print("Invalid message")
        reliable_send(ssl_client_socket,message_result)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="UROP"
)
cursor = db.cursor()

host = 'localhost'
port = 12345


context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.minimum_version = ssl.TLSVersion.TLSv1_2
context.maximum_version = ssl.TLSVersion.TLSv1_3
context.load_cert_chain(certfile="C:/Users/smitk/OneDrive/programs/python/projects/UROP/server-cert.pem", keyfile="C:/Users/smitk/OneDrive/programs/python/projects/UROP/server-key.pem")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(5)
online_users = {}
print(f"Server listening on {host}:{port}")

while True:
    client_socket, client_address = server_socket.accept()
    ssl_client_socket = context.wrap_socket(client_socket, server_side=True)
    print(f"Connection from {client_address} has been established.")
    client_thread = threading.Thread(target=handle_client, args=(ssl_client_socket,))
    client_thread.start()
    

        