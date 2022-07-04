class TraceResult:
    route: str  # ipv4-адрес хоста
    n: int  # номер хоста в трассировке
    net_name: str  # имя сети
    as_zone: str  # номер автономной системы
    country: str  # страна
    is_local: bool  # ip-адрес в трассировке является локальным

    def __init__(self, route, n, net_name, as_zone, country, is_local):
        self.route = route
        self.n = n
        self.net_name = net_name
        self.as_zone = as_zone
        self.country = country
        self.is_local = is_local

    def get_string_representation(self):
        result = f'{self.n}. {self.route}\r\n'
        if self.is_local:
            return result + ' local\r\n\r\n'
        info = []
        if self.net_name:
            info.append(self.net_name)
        if self.as_zone:
            info.append(self.as_zone[2:])
        if self.country and self.country != 'EU':
            info.append(self.country)
        if len(info) > 0:
            return result + ', '.join(info) + '\r\n'
        return result
