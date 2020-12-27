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

A client should send an OSC message to the server following the format:

```
{
'path': '/oscrouter/register',
'arguments': userName, userPassword, groupName, groupPassword, aRandomId
}
```

On a successful connection the server will reply with the following message:

```
{
'path': '/oscrouter/register',
'arguments': userName, aRandomId
}
```

The `userName` is created with the given `userPassword` inside the given `groupName`. 

For both the `userName` and `groupName` if one already exists the server will try to authenticate with the correspondent password, or fail if the password doesn't match.

Once the user is authenticated in a group (the `/oscrouter/register` message is sent back), you can start sending messages to the server. Any messages sent to the server from that point will be forwarded to all the users in the same group. 

It is also possible to send private messages by sending a message like:

```
{
'path': '/oscrouter/private',
'arguments': userName, path, msg_arguments,
}
```

Your client will receive private messages in the `/oscrouter/private` address as well. For every user leaving or joining the group the client also receives the current list of users as `/oscrouter/userlist`.
