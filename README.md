# OSC routing over TCP

A OSC message router over TCP designed with SuperCollider in mind

Connect multiple SuperCollider instances over the internet and exchange messages between them.

Includes also a front-end (html) to check the status of the router, who is connected, messages being routed, and so on.


**server/** folder is where the server code is. It is written in Python (>=3.7) and uses asyncio and python-osc.

**supercollider/** folder holds a SuperCollider class that can be used to join the network. See **examples/** folder.
