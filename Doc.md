# CODE Doc

- ## Code Description & Design Decision:

    - Code is done by `Python`
    - Use `argparse` to parse arguments from command line
    -  `main()` function is used to 
        - Create a thread pool
        - Build up a welcome socket (to listen to clients' requests)
        - Once there is a request, create a client_sock for communication between client and host
        - Check HTTP Request format that client sent, reply `400 Bad Request` if the format is incorrect
            - Here we just check whether each request line are either an empty line(ends with /n) or ends with /r/n.
        - If request is `CONNECT`, get request url and port,close client_sock when it is not `CONNECT`
        - Perform blacklisting if needed. (Reply with `403 Forbidden` if the site is blacklisted)
        - Assign one thread do the HTTPS data forwarding task after we ensure that the URL is valid and not blacklisted
    - Use `ThreadPool` to control multithreading, it makes the control of maximum thrread number very easy by just setting the `max_workers` value.
    - `ClientHandler(client_sock: socket, request_address: (str, int), http_version: str)` function is the so called `WorkerFucntion`. It is the thread work assigned by `main()` which does:
        - Connect to the server that client requested (server_sock)
        - Send greeting msg to client (200 Connection established)
        - Main transmission (Nothing but a data forwarding between client and server)
            - Here we use select.select to monitor the IO of `client_sock` and `server_sock`, if any socket has error, close the transection. Otherwise, if one socket received data, send it to another socket. If no transmission happends within **time_out** second (defined in line 18), close the two connections.
        - Count the byte traffic amount from server to proxy and the time taken, display it if telemetry function is ON.

- ## Difference between HTTP/1.0 and HTTP/1.1

    > Because for HTTP/1.0, after each request response pair, the HTTP connection will be stopped and in order to fetch the rest of the data from the same host, browser needs to create a connection with the host again.
    >
    > For HTTP/1.1, after each request response pair, if the browser realized that more data needes to be fetched from the same host before the timeout of the connection, it can directly send another request from the host using the same socket without the need of re-connection.

- ## Proof the difference using telemetry in practice

    ```
    [HTTP/1.0] Visit www.amazon.com
    Hostname: www.comp.nus.edu.sg, Size: 104871 bytes, Time: 6911.225 ms
    Hostname: www.youtube.com, Size: 1325 bytes, Time: 5027.756 ms
    Hostname: images-na.ssl-images-amazon.com, Size: 50936 bytes, Time: 34.426 ms
    Hostname: amazon.com, Size: 6119 bytes, Time: 5717.845 ms
    Hostname: safebrowsing.googleapis.com, Size: 1854 bytes, Time: 25.876 ms
    Hostname: incoming.telemetry.mozilla.org, Size: 526 bytes, Time: 6481.251 ms
    Hostname: assoc-na.associates-amazon.com, Size: 6306 bytes, Time: 5751.490 ms
    Hostname: completion.amazon.com, Size: 6631 bytes, Time: 5766.776 ms
    Hostname: fls-na.amazon.com, Size: 6001 bytes, Time: 752.851 ms            <- This two
    Hostname: fls-na.amazon.com, Size: 461 bytes, Time: 768.467 ms             <- This two
    Hostname: images-na.ssl-images-amazon.com, Size: 259605 bytes, Time: 9594.528 ms
    ...
    ```

    ```
    [HTTP/1.0] Visit www.amazon.com
    Hostname: incoming.telemetry.mozilla.org, Size: 438 bytes, Time: 5247.340 ms
    Hostname: images-na.ssl-images-amazon.com, Size: 29933 bytes, Time: 5110.865 ms
    Hostname: images-na.ssl-images-amazon.com, Size: 5758 bytes, Time: 5033.203 ms
    Hostname: m.media-amazon.com, Size: 5756 bytes, Time: 5031.271 ms
    Hostname: m.media-amazon.com, Size: 561866 bytes, Time: 5123.755 ms
    Hostname: www.amazon.com, Size: 109353 bytes, Time: 8296.076 ms
    Hostname: fls-na.amazon.com, Size: 11459 bytes, Time: 8117.970 ms         <- This one
    Hostname: spl.zeotap.com, Size: 4094 bytes, Time: 5114.750 ms
    Hostname: www.imdb.com, Size: 6999 bytes, Time: 5248.609 ms
    Hostname: s.amazon-adsystem.com, Size: 5433 bytes, Time: 6639.471 ms
    ...
    ```

    > We can see that when it is running under HTTP/1.0, when browser want to access fls-na.amazon.com to fetch 2 different files, the only way it can do it to create HTTP connection twice. However, when under HTTP/1.1, it can fetch two files in-one-go without reconnection. However, do note that this is because the time difference of the two request is within the proxy's timeout value (It is set by us in the main.py file as 5s, you can change it by changing the **time_out** variable in line 18), if it is not within the range, then the HTTP connection between client and proxy (and also, the connection between proxy and the server host) will be closed and if 2nd file transfer is needed, then another connection must be conducted.