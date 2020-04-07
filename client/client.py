import socket
import sys
import os
import time


class MySocket:
    def __init__(self):
        self.client = None
        pass

    def create_socket(self):
        # socket.SOCK_STREAM is specifying TCP connection
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, host, port):
        self.client.connect((host, port))

    def send_get_request(self, request_message):
        self.client.send(request_message.encode())

    def send_conditional_get_request(self, request_message):
        self.client.send(request_message.encode())

    def get_response(self):
        return self.client.recv(4096)

    def close_socket(self):
        self.client.close()


def cache_response(file_name, response):
    file = open(file_name, 'w')
    file.write(response)
    file.close()


def is_file_cahced(file_name):
    return os.path.exists(f'cache/{file_name}')


def request_message(file_name, host, port, modified_date):
    request_line = f'GET /{file_name} HTTP/1.1\r\n'
    host = f'Host: {host}:{port}\r\n'
    modifed_since = ''
    blank_line = '\r\n'
    additional_headers = ''  # 'asd\r\nasd\r\nasd\r\n'
    if(modified_date):
        modifed_since = f'If-Modified-Since: {modified_date}\r\n'

    http_request_message = request_line + host + \
        additional_headers + modifed_since + blank_line

    return http_request_message


def get_modified_date(file_name):
    seconds = os.path.getmtime(f'cache/{file_name}')
    t = time.gmtime(seconds)
    last_mod_time = time.strftime("%a, %d %b %Y %H:%M:%S GMT\r\n", t)
    return last_mod_time


def parse_response(response, file_name):
    response = response.decode()
    headers = response.split('\r\n\r\n')
    response = response.split('\r\n')

    request_line = response[0]
    status_code = request_line.split(' ')[1]
    if(status_code == '200'):
        cache_response(f'cache/{file_name}', response[-1])
        print('Server Response Headers:', headers[0], sep='\n')
        print('\nServer Response Payload:', headers[1], sep='\n')
        pass
    elif(status_code == '304'):
        print('Server Response Headers:', request_line, sep='\n')
        pass
    elif(status_code == '404'):
        print('Server Response Headers:', request_line, sep='\n')
        pass


def main():
    try:
        arguments = sys.argv[1].split('/')
        file_name = arguments[1]
        host, port = arguments[0].split(':')
        port = int(port)
    except IndexError:
        print('Please provide arguments as "hostname:port/<filename>,html"')
        sys.exit(1)

    socket = MySocket()
    socket.create_socket()
    socket.connect(host=host, port=port)

    if(is_file_cahced(file_name=file_name)):
        modified_date = get_modified_date(file_name)
        http_message = request_message(file_name, host, port, modified_date)
        socket.send_conditional_get_request(http_message)
    else:
        modified_date = None
        http_message = request_message(file_name, host, port, modified_date)
        socket.send_get_request(http_message)

    print('Client Request Headers', http_message, sep=':\n')

    response = socket.get_response()
    parse_response(response, file_name)

if __name__ == "__main__":
    main()
    pass
