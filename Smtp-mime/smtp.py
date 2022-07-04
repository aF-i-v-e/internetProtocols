import os
import ssl
from pathlib import Path
import base64
import getpass

from SMTPException import SMTPException
from file import File
from letter import Letter
from socket import AF_INET, SOCK_STREAM, socket


class SMTP:
    def __init__(self, ssl: bool, server: str, to: str, login: str,
                 subject: str, auth: bool, verbose: bool, directory: str):
        self.ssl = ssl
        server_port = server.split(':')
        if len(server_port) != 2:
            raise ValueError('Incorrect address '
                             '(must be in "server:port" format)')
        self.server = server_port[0]
        self.port = int(server_port[1])
        self.to = to
        self.login = login
        self.subject = subject
        self.directory = Path(directory)
        self.verbose = verbose
        self.commands = [f'EHLO {self.get_hostname()}\n',
                         f'MAIL FROM: <{self.login}>\nRCPT TO: '
                         f'<{self.to}>\nDATA\n']
        if auth:
            password = getpass.getpass()
            base_login = base64.b64encode(self.login.encode('utf-8')) \
                .decode('utf-8')
            base_passwd = base64.b64encode(password.encode('utf-8')) \
                .decode('utf-8')
            self.commands.insert(1, 'auth login\n')
            self.commands.insert(2, f'{base_login}\n')
            self.commands.insert(3, f'{base_passwd}\n')

    def get_hostname(self):  # модифицируем логин(from), чтобы получить имя хоста для EHLO
        return self.login.replace("@", ".")

    def create_letter(self) -> str:
        letter = Letter()
        letter.set_header(self.login, self.to, self.subject)
        files = [File(self.directory / x)  # формируем массив файликовс картинками из переданной директории
                 for x in os.listdir(self.directory)
                 if x.endswith('.jpg')]
        for i in range(len(files)):
            letter.set_content(files[i], i == len(files) - 1)  # передаем файл
            # и флаг о том, является ли он последним файлом в директории
        return letter.get_letter()

    def receive_message(self, sock: socket):  # получить сообщение
        msg = sock.recv(1024).decode('utf-8')
        msg_parts = msg.split('\n')[:-1]  # беру последнюю строчку присланного сообщения
        last_code = msg_parts[-1][0:3]  # беру код ответа - первые 3 символа
        last_msg = msg_parts[-1][4:]  # беру само сообщение сервера
        if last_code[0] == '5':
            raise SMTPException(msg)  # код начинается с 5: неустранимая ошибка
        if self.verbose:
            if last_code == '334':  # 3- сервер ждет доп информации
                # + присылает закодированное в base64 слово: Login или Password
                last_msg = base64.b64decode(f'{last_msg}==').decode('utf-8')
                msg = f'{last_code} {last_msg}'
            print(f'<- {msg}')

    def send_message(self, sock: socket, msg: str):
        if self.verbose:
            print(f'-> {msg}')
        sock.send(msg.encode())

    def run(self):
        with socket(AF_INET, SOCK_STREAM) as sock:
            sock.connect((self.server, self.port))
            self.receive_message(sock) #потому что сначала должны получить сообщение от сервера
            if self.ssl: #договариваемся что будем общаться по защищенному соединению
                self.send_message(sock,
                                  f'EHLO {self.get_hostname()}\n')
                self.receive_message(sock)
                self.send_message(sock, 'starttls\n')
                self.receive_message(sock)
                sock = ssl.wrap_socket(sock)
            for command in self.commands:
                self.send_message(sock, command)
                self.receive_message(sock)
                if 'DATA' in command:
                    sock.send(self.create_letter().encode())
                    self.receive_message(sock)
