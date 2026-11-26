import socket


def find_free_port(start_port=5550, end_port=5559):
    """
        **EN**: Finds the first available TCP port within the specified range.

        **RU**: Находит первый свободный TCP-порт в заданном диапазоне.

        **Args / Параметры:**
        - `start_port` (`int`) — **EN**: Start of the range. | **RU**: Начало диапазона.
        - `end_port` (`int`) — **EN**: End of the range. | **RU**: Конец диапазона.

        **Returns / Возвращает:**
        - `int` — **EN**: Available port number. | **RU**: Номер свободного порта.

        **Raises / Исключения:**
        - `RuntimeError` — **EN**: If no ports are available. | **RU**: Если все порты в диапазоне заняты.
    """
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"Нет свободных портов в диапазоне {start_port}-{end_port}")