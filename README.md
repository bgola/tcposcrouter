# tcposcrouter

A OSC message router working over TCP, written specially to connect multiple supercollider clients over the internet and exchange messages between them.

There is also a front-end (html) to check the status of the router (who is connected, messages being router).


**server/** folder is where the server code is. It is written in Python (>=3.7) and uses asyncio and python-osc.

**supercollider/** folder holds a SuperCollider class that can be used to join the network. See **examples/** folder.
