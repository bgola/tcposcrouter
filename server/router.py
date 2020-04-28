from pythonosc.osc_message import OscMessage
from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.dispatcher import Dispatcher

from asyncio import StreamWriter, StreamReader

from typing import Dict, List

import asyncio, struct, time, random
import websockets
import socket
import logging


class Connection:
    writer: StreamWriter
    reader: StreamReader

    notification_callbacks = []

    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.dispatcher: Dispatcher = Dispatcher()
        self.dispatcher.map("/oscrouter/register", self.register)
        self.dispatcher.map("*", self.call_notification_callbacks)
        self.user = None
        print(f"New connection from '{self.peername}'")

    def call_notification_callbacks(self, address, *args):
        if "/oscrouter/" in address: 
            return
        for cb in Connection.notification_callbacks:
            cb(self.user, address, *args)

    def register(self, address, *args):
        username = args[0]
        password = args[1]
        sid = args[2]

        user = User.index.by_name.get(username, None)
        
        if user is None:
            # new user
            user = User()

        if user.auth(username, password):
            self.user = user
            self.user.connections.append(self)
            User.index.register(self.user)

            # Send reply message confirming register
            address = f"/oscrouter/register/{username}/{sid}"
            self.send_message(address)
            return

    @property
    def peername(self):
        return self.writer.get_extra_info('peername')
    
    @property
    def on(self):
        return self.reader and (not self.reader.at_eof())

    async def read_message(self):
        try:
            data = await self.reader.readexactly(4)
        except (
                asyncio.exceptions.IncompleteReadError,
                asyncio.exceptions.TimeoutError):
            # connection dropped maybe
            return b''
        length = struct.unpack('>i', data)[0]
        try:
            data = await self.reader.readexactly(length)
        except (
                asyncio.exceptions.IncompleteReadError,
                asyncio.exceptions.TimeoutError):
            # connection dropped maybe
            return b''
        return data
 
    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

    async def try_register(self):
        # Called the first time to process the initial registering message
        await self.process_messages()

    async def process_messages(self):
        data = await self.read_message()
        if not data:
            return
        self.dispatcher.call_handlers_for_packet(data, self.peername)
        await self.writer.drain()

    async def join(self):
        self.add_route_map()

        while True and self.on:
            await self.process_messages()
            last_alive = time.time()

        try:
            self.user.connections.remove(self)
        except ValueError:
            pass
        
        if not self.user.connections:
            # wait a bit if we get any new connection
            await asyncio.sleep(30)
            if not self.user.connections:
                print(f"{self.user} left the building")
                User.index.unregister(self.user)

        await self.close()

    def add_route_map(self):
        self.dispatcher.map('*', self.user.route)

    def send_message(self, address, *args):
        msg = OscMessageBuilder(address)
        for arg in args:
            msg.add_arg(arg)
        data = msg.build().dgram
        length = len(data)
        data = struct.pack('>i', length) + data
        # print(f"Sending to {self.peername}: {data}")
        self.writer.write(data)


class UserRegistry:
    def __init__(self):
        self.by_name: Dict[str, User] = {}
        self.by_connection: Dict[Connection, User] = {}
        self.notification_callbacks = []

    def register(self, user):
        new_user = False
        if user.name not in self.by_name.keys():
            self.by_name[user.name] = user
            new_user = True

        for conn in user.connections:
            self.by_connection[conn] = user

        if new_user:
            print(f"New user '{user}' registered")
        else:
            print(f"User '{user}' updated")
        self.notify_cbs()

    def notify_cbs(self):
        for cb in self.notification_callbacks:
            cb([ f"{user.name}[{len(user.connections)}]" for user in self.by_name.values()])

    def unregister(self, user):
        del self.by_name[user.name]
        for conn in user.connections:
            del self.by_connection[conn]
        self.notify_cbs()


class User:
    name: str
    password: str
    connections: List[Connection]
    
    index: UserRegistry = UserRegistry()

    def __init__(self):
        self.name = ""
        self.password = ""
        self.connections = []

    def __str__(self):
        return self.name

    @property
    def authenticated(self):
        return self.name != "" and self.password != ""

    def auth(self, name, password):
        if self.name == "" and self.password == "":
            print(f"Creating new user with '{name}'")
            self.name = name
            self.password = password
            return True

        if self.name != name or self.password != password:
            print(f"User '{self.name}' failed to authenticate.")
            return False
        
        print(f"User '{self.name}' authenticated.")
        return True

    def send_message(self, address, *args):
        for connection in self.connections:
            connection.send_message(address, *args)

    def route(self, address, *args):
        print(f"routing message '{address}' with args: '{args}' from '{self.name}'")
        for user in User.index.by_name.values():
            if user.name == self.name:
                continue
            user.send_message(address, *args)
 

class Group:
    name: str
    password: str
    users: List[User]

    def __init__(self, name: str, password: str):
        self.name = name
        self.password = password


async def handle_new_conn(reader, writer):
    connection = Connection(reader, writer)
    await connection.try_register()

    if connection.user and connection.user.authenticated:
        await connection.join()
    
    if connection.on:
        await connection.close()
    print("Closed the connection")


async def handle_websocket(websocket, path):
    print("New websocket connection")
    msgs = []
    def msg_ws(user, address, *args):
        print(f"Websocket callback called with {user},{address},{args}")
        msgs.append((user, address, args))
    def user_ws(users):
        msgs.append(users)
    Connection.notification_callbacks.append(msg_ws)
    User.index.notification_callbacks.append(user_ws)
    User.index.notify_cbs()
   
    async def send_msgs():
        _msgs = msgs[:]
        for msg in _msgs:
            if len(msg) == 3:
                user, address, args = msg
                print(f"Sending msg to {websocket}... {user}, {address}, {args}")
                await websocket.send(f"mUser '{user}' sent to '{address}' with args: '{args}'")
            else:
                print(f"Sending user list to {websocket}... {msg}")
                await websocket.send(f"u{','.join(msg)}")
            msgs.remove(msg)
    
    try:
        while True:
            await send_msgs()
            await asyncio.sleep(0.1)
    except Exception as e:
        print("Probably leaving...")
        print(e)
    finally:
        Connection.notification_callbacks.remove(msg_ws)
        print("Left...")

async def main():
    if production:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    loop = asyncio.get_event_loop()
    server = await asyncio.start_server(
        handle_new_conn, '0.0.0.0', 55555)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    ws_server = await websockets.serve(handle_websocket, '0.0.0.0', 5680)

    async with server:
        await asyncio.gather(server.serve_forever(), ws_server.server.serve_forever())


asyncio.run(main())
