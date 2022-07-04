from tracert_info import TraceResult
from scapy.all import *
from scapy.layers.inet import IP, ICMP

russian_parameters_list = ('netname', 'country', 'origin')
foreign_parameters_list = ('NetName', 'Country', 'OriginAS')


class Tracer:
    def __init__(self, dist):
        self.ttl = 1  # время жизни пакета = кол-во промежуточных маршрутизаторов
        self.max_hops = 30  # максимально - 30 маршрутизаторов
        self.destination = socket.gethostbyname(dist)
        if self.destination == socket.gethostbyname('localhost'):
            self.max_hops = 1

    @staticmethod
    def get_whois_iana_data(addr):
        # Получение адреса нужного нам whois-сервера у iana
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as whois_sock:
            whois_sock.settimeout(1)
            whois_sock.connect((socket.gethostbyname('whois.iana.org'), 43))  # открываем соединение на 43 порт
            whois_sock.send(addr.encode(encoding='utf-8') + b'\r\n')
            try:
                iana_response = whois_sock.recv(1024).decode()
                whois_addr_start = iana_response.index('whois')
                whois_addr_end = iana_response.index('\n', whois_addr_start)
                whois_addr = iana_response[whois_addr_start:whois_addr_end]. \
                    replace(' ', '').split(':')[0]
                return whois_addr
            except (socket.timeout, ValueError):
                pass
        return ''

    # запрашиваем информацию об адресе и производим парсинг ответа от подходящего whois сервера
    def get_whois_data(self, addr: str) -> Optional[Dict]:
        whois_addr = self.get_whois_iana_data(addr)
        whois_data = {}  # словарик, в который запишем полученные нами даннные об адресе
        if not whois_addr:
            return
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as whois_sock:
            whois_sock.settimeout(2)
            whois_sock.connect((whois_addr, 43))
            whois_sock.send(addr.encode(encoding='utf-8') + b'\r\n')
            data = b''  # пустая строка в бинарном виде
            while True:  # получение ответа от whois сервера об итересущем нас адресе
                temp_data = whois_sock.recv(1024)
                if not temp_data:
                    break
                data += temp_data
            data = data.decode()
            whois_data = self.parse_who_is_answer(russian_parameters_list, data, whois_data)
            # это для России
            if len(whois_data) == 0:
                whois_data = self.parse_who_is_answer(foreign_parameters_list, data, whois_data)
            # это для заграницы
        whois_data['route'] = addr
        return whois_data

    def parse_who_is_answer(self, parameters_list, data, whois_data):
        # парсинг ответа от whois сервера
        for field in parameters_list:
            try:
                field_start = data.rindex(f'{field}:')
                field_end = data.index('\n', field_start)
                field_data = data[field_start:field_end]. \
                    replace(' ', '').split(':')[1]
                whois_data[field] = field_data
            except ValueError:
                continue
        return whois_data

    # сама логика трассировки - отправка пакета с ttl = 1, получение адреса, увеличение ttl на 1
    # и так далее пока не получим нужный нам адрес, заданный пользователем в командной строке
    def trace(self):
        n = 1
        is_end = False
        intermediate_address = self.destination
        while self.ttl <= self.max_hops:
            # отправка icmp пакета
            icmp_package = IP(dst=self.destination, ttl=self.ttl) / ICMP(type=8, code=0) / "icmpdata"
            ans, unans = sr(icmp_package, timeout=5)
            package_counter = 0  # количество пакетов с ответом
            for snd, rcv in ans:
                intermediate_address = rcv.src  # получаем промежуточный адрес
                package_counter += 1
                if snd.dst == intermediate_address:  # если промежуточный адрес = искомому адресу, то заканчиваем
                    is_end = True
                    break
            if package_counter == 0:
                print("{}. *\r\n\r\n".format(n))
                self.ttl += 1
                n += 1
                continue
            whois_data = self.get_whois_data(intermediate_address)  # получение информации об адресе
            trace_result = self.get_trace_result(intermediate_address, n, whois_data)  # на основе информации
            # формируем результат трассировки
            yield trace_result
            self.ttl += 1
            n += 1
            if is_end:
                break

    def get_trace_result(self, addr: str, n: int, data: Dict) -> TraceResult:
        # формируем результат в зависимости от формата ответа whois сервера
        is_local = data is None
        if is_local:
            return TraceResult(addr, n, '', '', '', is_local)
        if 'country' in data:
            return self.create_trace_result(addr, n, data, russian_parameters_list)
        return self.create_trace_result(addr, n, data, foreign_parameters_list)

    def create_trace_result(self, addr: str, n: int, data: Dict, parameters_list):
        # формируем результат трассировки с помощью полученных данных
        route = data.get('route', '')
        net_name = data.get(parameters_list[0], '')
        country = data.get(parameters_list[1], '')
        as_zone = data.get(parameters_list[2], '')
        return TraceResult(route, n, net_name, as_zone, country, False)
