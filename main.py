import concurrent.futures
import argparse
import socket
import select
import time

parser = argparse.ArgumentParser()
parser.add_argument("port", type=int)
parser.add_argument("-t", "--telemetry", type=int, default=0, choices=[0, 1])
parser.add_argument("-b", "--blacklist_file", type=str)

port = parser.parse_args().port
telemetry = parser.parse_args().telemetry
blacklist_file = parser.parse_args().blacklist_file

recv_buffer_size = 4096
max_threads = 8
time_out = 5


def ClientHandler(client_sock: socket, request_address: (str, int), http_version: str):
    server_sock = socket.create_connection(request_address)
    # Send greeting msg to client
    greeting_binary = f"HTTP/{http_version} 200 Connection established \r\n\r\n".encode()
    client_sock.sendall(greeting_binary)
    traffic_bytes = 0
    transmission_done = False
    start = time.time()
    # Main transmission (Nothing but a data forwarding between client and server)
    while not transmission_done:
        # Use select to monitor IO (Time out 5s to close the connect + print stat when transmission stops for 5s)
        read_list, write_list, exception_list = select.select([client_sock, server_sock], [],
                                                              [client_sock, server_sock], time_out)
        # When there are exceptions or there are nothing to read from
        if len(exception_list) > 0 or len(read_list) == 0:
            break
        for event in read_list:
            if event == client_sock:
                binary = client_sock.recv(recv_buffer_size)
                if not binary:
                    transmission_done = True
                    break
                server_sock.sendall(binary)
                # print(f"Client -> Host {binary}")
            elif event == server_sock:
                binary = server_sock.recv(recv_buffer_size)
                if not binary:
                    transmission_done = True
                    break
                # Count object length
                traffic_bytes += len(binary)
                client_sock.sendall(binary)
                # print(f"Host -> Client {binary}")
    # Close sockets
    client_sock.close()
    server_sock.close()
    end = time.time()
    if telemetry:
        print(f"Hostname: {str(request_address[0])}, Size: {traffic_bytes} bytes, Time: {(end - start) * 1000:.3f} ms")


def main():
    # Create thread pool
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_threads)
    # Bind to localhost
    welcome_sock = socket.socket()
    welcome_sock.bind(("", port))
    # Read blacklist info
    if blacklist_file:
        with open(blacklist_file) as file:
            blacklist = file.read().splitlines()
    while True:
        # Listen to the socket
        welcome_sock.listen(5)
        # Create a client_sock for communication between client and host
        client_sock, client_address = welcome_sock.accept()
        dataBinary = client_sock.recv(recv_buffer_size)
        if not dataBinary: continue
        dataList = dataBinary.split(b"\n")
        # Check HTTP Request format
        http_version = dataList[0][-4:-1].decode()
        for dataLine in dataList[:-1]:
            # print(dataLine[-1:])
            if dataLine[-1:] != b"\r":
                client_sock.sendall(f"HTTP/{http_version} 400 Bad Request \r\n\r\n".encode())
                client_sock.close()
                continue
        # Check whether it is CONNECT
        if dataList[0][0:7] == b"CONNECT":
            # print(f'Client -> Proxy : {str(dataBinary)}')
            # If CONNECT, get requestAddress
            request_address_list = dataList[0].split(b" ")[1].split(b":")
            host_address = (request_address_list[0].decode(), int(request_address_list[1]))
            # Check the blacklist
            blacklisted = False
            if blacklist_file:
                for blacklist_site in blacklist:
                    if blacklist_site in host_address[0]:
                        blacklisted = True
                        break
            # print(http_version)
            if blacklisted:
                client_sock.sendall(f"HTTP/{http_version} 403 Forbidden \r\n\r\n".encode())
                print(f"Site {host_address[0]} is blocked")
                client_sock.close()
                continue

            # Let one thread do the proxy task after we ensure that the URL is valid and not blacklisted
            executor.submit(ClientHandler, client_sock, host_address, http_version)
        # Close client_sock when not CONNECT
        else:
            client_sock.close()
    welcome_sock.close()


if __name__ == "__main__":
    main()
