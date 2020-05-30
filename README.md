# OSC routing over TCP

A OSC message router over TCP written in Python designed with SuperCollider in mind.

Connect multiple SuperCollider instances over the internet and exchange messages between them.

Includes also a front-end (html) to check the status of the router, who is connected, messages being routed, and so on.

# Installing 

You will need Python >= 3.7 together with websockets and python-osc python libraries.

```
$ pip install -r websockets python-osc
$ pip install -e git+http://github.com/bgola/tcposcrouter.git#egg=tcposcrouter
```

# Running

```
$ tcposcrouter -h
usage: tcposcrouter [-h] [--osc-port OSC_PORT] [--websocket-port WEBSOCKET_PORT] [--log-dir LOG_DIR] [--fullchain-pem FULLCHAIN_PEM] [--private-key PRIVATE_KEY]

Run the tcposcrouter server.

optional arguments:
  -h, --help            show this help message and exit
  --osc-port OSC_PORT   OSC port to listen
  --websocket-port WEBSOCKET_PORT
                        WebSocket port to listen
  --log-dir LOG_DIR     Path where to save logs
  --fullchain-pem FULLCHAIN_PEM
                        Path to SSL fullchain.pem (if using SSL for the websocket)
  --private-key PRIVATE_KEY
                        Path to SSL privkey.pem (if using SSL for the websocket)
```

By default it listens for OSC on the 55555 **TCP** port.

# Client

For a client example please check the SuperCollider class at:

https://github.com/aiberlin/HyperDisCo/blob/master/Classes/OSCRouterClient.sc

