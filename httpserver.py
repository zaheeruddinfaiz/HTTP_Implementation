# ash47@njit.edu
import socket
import sys
import os
import time
import datetime
import time
import sys


def main():
    try:
        host, port = sys.argv[1].split(':')
        port = int(port)
        serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serv.bind((host, port))
        serv.listen(5)
        print(f'Server is listening on host: {host} and port:{port}')
        start(serv)
    except IndexError:
        print('Please provide arguments as "hostname:port"')
        sys.exit(1)


def parse_request(client_message):
    client_message = client_message.split('\r\n')
    request_line = client_message[0]
    host = client_message[1]
    modified_since = ''
    for message in client_message[2:]:
        if(message.lower().find('if-modified-since') >= 0):
            modified_since = message
            break

    return(request_line, host, modified_since)


def get_current_date():
    obj = datetime.datetime.today()
    objTimeTuple = obj.timetuple()
    date = time.strftime("%a, %d %b %Y %H:%M:%S %Z GMT", objTimeTuple)

    return date


def get_modified_seconds(file_name):
    try:
        seconds = os.path.getmtime(f'resources/{file_name}')
    except FileNotFoundError:
        seconds = None

    return seconds


def convert_to_date(seconds):
    t = time.gmtime(seconds)
    last_mod_time = time.strftime("%a, %d %b %Y %H:%M:%S GMT", t)
    return last_mod_time


def response_message(status_code, status_phrase, file_name, content_size, payload):
    status_line = f'HTTP/1.1 {status_code} {status_phrase}\r\n'
    date = f'Date: {get_current_date()}\r\n'
    last_modified = f'Last-Modified: {convert_to_date(get_modified_seconds(file_name))}\r\n'
    content_length = f'Content-Length: {content_size}\r\n'
    content_type = 'Content-Type: text/html; charset=UTF-8\r\n'
    blank_line = '\r\n'
    body = payload

    response_message = status_line + date + last_modified + \
        content_length + content_type + blank_line + body

    return response_message


''' Used to get the resources'''


def get_resource_content(file_name):
    try:
        file_reader = open(f'resources/{file_name}', 'rb')
        content = file_reader.read()
    except FileNotFoundError:
        content = None
    except IsADirectoryError:
        content = None

    return content


def get_resource_name(request_line):
    try:
        file_name = request_line.split(' ')[1]
        file_name = file_name[1:]
    except IndexError:
        print('Request line format is incorrect. Aborting further action')
        file_name = None

    return file_name


def convert_to_secs(date):
    t = time.strptime(date, "%a, %d %b %Y %H:%M:%S %Z\r\n")
    secs = time.mktime(t)
    return secs


def handle_conditional_response(conn, request_line, modified_since):

    file_name = get_resource_name(request_line=request_line)

    modified_since_date = modified_since.split(': ')[1]
    # modified_since_date = modified_since_date[:-4]
    modified_since_date += '\r\n'
    client_secs = convert_to_secs(modified_since_date)

    server_secs = get_modified_seconds(file_name)
    server_date = convert_to_date(server_secs)
    server_date += '\r\n'
    server_secs = convert_to_secs(server_date)
    payload = get_resource_content(file_name=file_name)
    payload = payload.decode()
    if(server_secs is None):
        message = conditional_response_message(
            status_code=404, status_phrase='File not found')
    if(server_secs < client_secs):
        message = conditional_response_message(
            status_code=304, status_phrase='Not Modified')

    else:
        message = response_message(
            status_code=200, status_phrase='OK', file_name=file_name, content_size=len(payload), payload=payload)

    conn.send(message.encode())


def conditional_response_message(status_code, status_phrase):
    request_line = f'HTTP/1.1 {status_code} {status_phrase}\r\n'
    date = get_current_date()
    content_lenght = ''
    if(status_code == 404):
        content_lenght = '0\r\n'

    conditional_response_message = request_line + date + content_lenght

    return conditional_response_message


def handle_response(conn, request_line, host, modified_since):
    file_name = get_resource_name(request_line=request_line)
    # Request line does not have correct format
    # if(file_name is None):
    #     break
    content = get_resource_content(file_name=file_name)
    # print(content)

    if(content is not None):
        # NO need to encode, as the data is already in byte format
        message = response_message(
            200, 'OK', file_name, len(content), content.decode())
    else:
        message = conditional_response_message(404, 'Not Found')

    conn.send(message.encode())


def start(serv):
    while True:
        conn, addr = serv.accept()
        from_client = ''
        # file = open('res.html', 'rb')
        while True:
            try:
                client_message = conn.recv(4096)
                if not client_message:
                    break

                request_line, host, modified_since = parse_request(
                    client_message.decode())
                if(modified_since == ''):
                    handle_response(conn, request_line, host, modified_since)
                else:
                    handle_conditional_response(
                        conn, request_line, modified_since)

                # print(request_line, host, modified_since, sep='\n')
            except ConnectionResetError:
                pass
    conn.close()
    print('client disconnected')


if __name__ == "__main__":
    main()
