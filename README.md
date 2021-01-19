# OSC routing over TCP

An OpenSoundControl message router over TCP written in Python designed with SuperCollider in mind.

Connect multiple SuperCollider instances over the internet and exchange messages between them.

While tcposcrouter was developed with SuperCollider in mind, it is possible to use it with any other software that supports OSC over TCP.

# OSC specification

tcposcrouter supports both spec-1.0 and spec-1.1 in regards to framing the messages for sending over TCP stream.

See: [https://forum.renoise.com/t/osc-via-tcp-has-no-framing/42459 for an interesting discussion].

For example, SuperCollider implements OSC spec-1.0 while PureData implements spec-1.1 (with mrpeach external). 

See the examples folder for example in both SuperCollider and PureData. 

Notice that tcposcrouter will open two ports by default, one for each spec version, but the internal routing/user/group state is shared between them.

# Installing 

You will need Python >= 3.7 together with python-osc python library.

Easiest way to install is to get it from PyPI:

```
$ pip install tcposcrouter
```

# Running

```
$  tcposcrouter -h
usage: tcposcrouter [-h] [--osc-port OSC_PORT] [--osc11-port OSC11_PORT] [--disable-osc10] [--disable-osc11] [--log-dir LOG_DIR]

Run the tcposcrouter server.

optional arguments:
  -h, --help            show this help message and exit
  --osc-port OSC_PORT   OSC port to listen
  --osc11-port OSC11_PORT
                        OSC port to listen using SLIP encoding
  --disable-osc10       Disables data length prefix (OSC spec-1.0)
  --disable-osc11       Disables SLIP encoding (OSC spec-1.1)
  --log-dir LOG_DIR     Path where to save logs
```



By default it listens for OSC on the 55555 **TCP** port.

# Client

For a client example please check the SuperCollider class at:

https://github.com/aiberlin/HyperDisCo/blob/master/Classes/OSCRouterClient.sc

A client should send an OSC message to the server following the format:

```
/oscrouter/register,ssssi,userName,userPassword,groupName,groupPassword
```

The `ssssi` is the OSC format to tell that the arguments are 4 strings and 1 integer.

On a successful authentication the server will reply with the following message:

```
/oscrouter/register/userName
```

The `userName` is created with the given `userPassword` inside the given `groupName`.

For both the `userName` and `groupName` if one already exists the server will try to authenticate with the correspondent password, or fail if the password doesn't match.

Once the user is authenticated in a group (the `/oscrouter/register` message is sent back), you can start sending messages to the server. Any messages sent to the server from that point will be forwarded to all the users in the same group. 

It is also possible to send private messages by sending a message like:

```
/oscrouter/private,ss,userName,address
```

Followed by as many arguments as you want. So `/oscrouter/private,ssifs,userName,address,10,123.30,hello` is a valid private message.

Your client will receive private messages in the `/oscrouter/private` address as well. For every user leaving or joining the group the client also receives the current list of users as `/oscrouter/userlist`.
