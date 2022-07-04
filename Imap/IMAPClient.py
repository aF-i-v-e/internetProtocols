import base64
from _socket import timeout, gaierror
import getpass
from typing import List
import socket
import ssl

from IMAPException import IMAPException
from WrongPortException import WrongPortException

passWord = "TV23rL8gmZWQACeGTuPY"


class IMAP:
    def __init__(self, ssl_: bool, server: str, n: List[str], user: str):
        self.ssl = ssl_
        server_port = server.split(':')
        if len(server_port) != 2:
            raise ValueError('Incorrect address '
                             '(must be in "server:port" format)')
        self.server = server_port[0]
        self.port = int(server_port[1])
        if len(n) == 0 or len(n) > 2 or len(n) == 2 and \
                (int(n[0]) > int(n[1]) or int(n[0]) < 0 or int(n[1]) < 0):
            raise ValueError('Incorrect letter interval')
        self.interval = n
        self.user = user
        self.start_token = 'A001'

    def run(self):
        sock = self.create_sock()
        try:
            self.receive_message(sock)
        except timeout:
            raise gaierror
        self.send_message(sock, f'{self.start_token} LOGIN '
                                f'{self.user} '
                                f'{getpass.getpass()}\n')
        login_response = self.receive_message(sock)
        if 'NO' in login_response:  # аутентификация прошла неправильно
            raise IMAPException(login_response[5:])
        self.send_message(sock,
                          f'{self.start_token} LIST \"\" *\n')  # получение списка всех почтовых ящиков клиента
        list_response = self.receive_message(sock).split('\n')[:-1]
        folders = []
        for response in list_response:
            if response.startswith("* LIST"):
                folders.append(response[response.find('/') + 4:-2])
        for folder in folders:
            self.select_group(sock, folder)

    def receive_message(self, sock: socket):  # получить сообщение
        data = bytearray()
        try:
            while True:
                received_data = sock.recv(1024)
                data.extend(received_data)
                if received_data.startswith(self.start_token):  # ответ сервера может быть  многострочным
                    # последнее сообщение от сервера заканчивается на тот токен, с которым оправляли запрос
                    break
        except timeout:
            pass
        finally:
            message = data.decode('utf-8')  # декодировать поток байтов в строковый объект
            # print(message)
            return message

    def send_message(self, sock: socket, msg: str):
        sock.send(msg.encode('utf-8'))  # закодировать строку в байты

    def create_sock(self):  # создание сокета
        if self.port != 993 and self.port != 143:  # т.к. imap работает только с 993 и 143 портом
            raise WrongPortException(str(self.port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.ssl:
            sock.connect((self.server, 993))
            return ssl.wrap_socket(sock)
        sock.connect((self.server, 143))
        return sock

    def select_group(self, sock: socket, folder: str):
        number_str = ''
        while 'EXISTS' not in number_str:  # сообщение типа кол-во сообщений EXISTS
            self.send_message(sock, f'{self.start_token} SELECT {folder}\n')  # выбрать почтовый ящик
            number_str = self.receive_message(sock).split('\n')[
                1]  # сервер описывает состояние почнового ящика 'вида кол-во сообщений EXISTS'
        print(f'{folder} FOLDER')
        letters_number = int(number_str.split(' ')[1])  # количество писем
        letter_range = self.get_range(letters_number)  # получаем нужный диапазон с учетом пользовательского ввода
        for i in letter_range:
            self.send_message(sock,
                              f'{self.start_token} FETCH {i} '  # Возвращает указанные части указанных сообщений i - номер сообщения
                              f'(FLAGS FULL)\n')  # интересуют сообщения со всеми флагами(и просмотренные, и непросмотренные)
            headers = self.receive_message(sock)
            if not headers or '(nothing matched)' in headers:
                break
            self.get_headers(headers)  # получаем заголовки писем
            self.get_body(headers)  # получение тела письма
        print()

    def get_range(self, letters_number: int):  # получение диапазона писем, который нас интересует
        if self.interval == ['-1']:
            return range(letters_number, 0, -1)
        if len(self.interval) == 1:
            return range(letters_number,
                         max(0, letters_number - int(self.interval[0])), -1)
        return range(letters_number - int(self.interval[0]) + 1,
                     letters_number - int(self.interval[1]), -1)

    def get_headers(self, headers: str):
        date_str = headers[headers.find("INTERNALDATE") + 14:]  # внутренняя дата сообщения.
        date = date_str[:date_str.find('"')]
        size_str = headers[headers.find("RFC822.SIZE") + 12:]  # размер сообщения
        size = size_str[:size_str.find(' ')]
        envelope = headers[headers.find("ENVELOPE") + 9:  # структура заголовка сообщения
                           headers.find('BODY') - 1]
        # "NIL" представляет собой указание на отсутствие каких-то определенных данных
        subj_str = envelope[36:] if envelope[35:38] != 'NIL' \
            else "- "
        subj = self.get_subject(subj_str[:subj_str.find('"')]) # тема письма
        from_str = envelope[envelope.find('((') + 2:
                            envelope.find('))')].split(' ')
        from_addr = self.get_addr(from_str)  # отправитель письма
        to_str = envelope[envelope.rfind('((') + 2:
                          envelope.rfind('))')].split(' ')
        to_addr = self.get_addr(to_str)  # получатель письма
        print(f'From: {from_addr} To: {to_addr} Subject: {subj} '
              f'{date} Size: {size}')

    # получение адреса отправителя/получателя письма из строки
    # чтобы в результате получить, например, ee-tester@mail.ru <Евгений Елькин>
    def get_addr(self, addr_str: List[str]):
        source_name = self.get_source_name(addr_str)
        return f'{addr_str[-2][1:-1]}@{addr_str[-1][1:-1]} ' \
               f'<{source_name}>'

    # получение информации о теле письма - количество вложений
    def get_body(self, headers: str):
        body = headers[headers.find('BODY') + 7:headers.rfind(')')]
        body_parts = body.split(')(')
        attaches = []
        for part in body_parts:
            if part.find("name") == -1:
                continue
            name = part[part.find("name") + 7:part.find('")')]
            encoding = '"base64"' if '"base64"' in part \
                else '"8bit"'
            attach_size = int(part[part.find(encoding) + 9:]
                              .split(' ')[0].replace(')', ''))
            attaches.append((name, attach_size))
        print(f'{len(attaches)} attaches: {attaches}')

    def get_source_name(self, addr_str):
        source_name = addr_str[0]
        if source_name[1:3] == '=?':
            coding = self.get_coding(3, source_name)
            name_in_transport_coding = source_name[3 + len(coding) + 3: -1]  # 3: "'=?" + длина названия кодировки
            # Плюс 3: ?B? и до -1 т. к. не берем последнюю кавычку
            return base64.b64decode(name_in_transport_coding) \
                .decode(coding)
        else:
            return ' '.join(addr_str
                            [:addr_str.index("NIL")])[1:-1] if "NIL" in addr_str else ''

    def get_subject(self, subject):
        if subject[:2] == '=?':
            coding = self.get_coding(2, subject)
            subject = base64.b64decode(subject[2 + len(coding) + 3:]).decode(coding)
            return subject.replace('\n', '\\n')
        return subject

    def get_coding(self, delta, str):
        return str[delta: str[delta:].index('?') + delta]