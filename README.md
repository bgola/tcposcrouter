# OSC routing over TCP

An OpenSoundControl message router over TCP written in Python designed with SuperCollider in mind.

Connect multiple SuperCollider instances over the internet and exchange messages between them.

# Installing 

You will need Python >= 3.7 together with python-osc python library.

Easiest way to install is to get it from PyPI:

```
$ pip install tcposcrouter
```

# Running

```
$ tcposcrouter -h
usage: tcposcrouter [-h] [--osc-port OSC_PORT] [--log-dir LOG_DIR]

Run the tcposcrouter server.

optional arguments:
  -h, --help            show this help message and exit
  --osc-port OSC_PORT   OSC port to listen
  --log-dir LOG_DIR     Path where to save logs
```

By default it listens for OSC on the 55555 **TCP** port.

# Client

For a client example please check the SuperCollider class at:

https://github.com/aiberlin/HyperDisCo/blob/master/Classes/OSCRouterClient.sc

