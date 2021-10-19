# HTTPS-Proxy

### Execution Guidance

``````
If need the blocklist function, add the blacklisted websites line by line into a txt file (eg: blacklist.txt) and then use its name in the following shell command.
``````

```shell
python3 main.py 6664 1 -t 1 -b blacklist.txt
```

```
first arg: [int] (mandantory) port number
second arg: [int] (default = 0) whether to enable telemetry. O -> disable, 1 -> enable
third arg: [str] (default = None) blacklist file location. if don't provide then disable blacklist function
PS: Please provide the file under the project directory, that is, the same directory as main.py
```

#### Example of execution command

```shell
#Run the proxy underr port 6664, enable telemetry, enable blacklist function (sites in blacklist.txt)
python3 main.py 6664 -t 1 -b blacklist.txt
```

```shell
#Run the proxy underr port 6664, disable telemetry, enable blacklist function (sites in blacklist.txt)
#Use
python3 main.py 6664 -t 0 -b blacklist.txt
#Or just omit the -t arg
python3 main.py 6664 -b blacklist.txt
```

```shell
#Run the proxy underr port 6664, enable telemetry, disable blacklist function
python3 main.py 6664 -t 1
```

```shell
#Run the proxy underr port 6664, disable telemetry, disable blacklist function (sites in blacklist.txt)
#Use
python3 main.py 6664 -t 0 -b blacklist.txt
#Just omit the -t arg
python3 main.py 6664 -b blacklist.txt
```



### Difference between HTTP/1.0 and HTTP/1.1

> Because for HTTP/1.0, after each request response pair, the HTTP connection will be stopped and in order to fetch the rest of the data from the same host, browser needs to create a connection with the host again.
>
> For HTTP/1.1, after each request response pair, if the browser realized that more data needes to be fetched from the same host before the timeout of the connection, it can directly send another request from the host using the same socket without the need of re-connection.

### Proof the difference using telemetry in practice

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

