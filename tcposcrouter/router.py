from pythonosc.osc_message import OscMessage
from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.dispatcher import Dispatcher

from asyncio import StreamWriter, StreamReader

from typing import Dict, List, Optional

import asyncio, struct, time, random
import logging
import socket
import json

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
        self._leave = False
        self._to_write = asyncio.Queue()
        self._reader_task = asyncio.create_task(self._reader_coro())
        self._writer_task = asyncio.create_task(self._writer_coro())
        logging.info(f"New connection from '{self}'")

    def __str__(self):
        if self.user:
            return f"{self.user}[{self.peername}]"
        else:
            return str(self.peername)

    def call_notification_callbacks(self, address, *args):
        if "/oscrouter/" in address:
            return
        for cb in Connection.notification_callbacks:
            cb(self.user, address, *args)

    def register(self, address, *args):
        username = str(args[0])
        password = str(args[1])

        if len(args) < 5:
            logging.warning(f"{self} is trying to register without a group!! Fallback to default group.")
            groupname = 'oscrouter'
            grouppassword = 'oscrouter'
            sid = args[2]
        else:
            groupname = str(args[2])
            grouppassword = str(args[3])
            sid = args[4]

        group = Group.index.get(groupname, None)

        if group is None:
            group = Group(groupname, grouppassword)
        
        if not group.auth(groupname, grouppassword):
            logging.info(f"User '{username}' failed to join group '{group}'. Wrong group password.")
            return

        user = group.users.by_name.get(username, None)
        
        if user is None:
            # new user
            user = User()
            user.group = group

        if user.auth(username, password):
            self.user = user
            self.user.connections.append(self)
            self.user.group.users.update(self.user)

            # Send reply message confirming register
            address = f"/oscrouter/register/{username}/{sid}"
            self.send_message(address)
            return

    @property
    def peername(self):
        return self.writer.get_extra_info('peername')

    @property
    def on(self):
        return not self._leave and self.reader and (not self.reader.at_eof())

    async def read_message(self):
        try:
            data = await self.reader.readexactly(4)
        except (
                asyncio.exceptions.IncompleteReadError,
                TimeoutError,
                ConnectionResetError,
                OSError,
                BrokenPipeError) as e:
            # connection dropped maybe
            return b''
        length = struct.unpack('>i', data)[0]
        try:
            data = await self.reader.readexactly(length)
        except (
                asyncio.exceptions.IncompleteReadError,
                ConnectionResetError,
                TimeoutError,
                OSError,
                BrokenPipeError) as e:
            return b''
        except Exception as e:
            logging.exception("Error while reading from TCP socket")
            return b''
        return data

    async def close(self):
        if not (self._writer_task.done() or self._writer_task.cancelled()):
            self._writer_task.cancel()
        if not (self._reader_task.done() or self._reader_task.cancelled()):
            self._reader_task.cancel()
 
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except (BrokenPipeError,
                TimeoutError,
                OSError) as e:
            pass
        except Exception as e:
            logging.exception("Exception when closing..")

    async def try_register(self):
        # Called the first time to process the initial registering message
        await self.process_messages()

    async def process_messages(self):
        done, unfinished = await asyncio.wait((self._reader_task, self._writer_task), return_when=asyncio.FIRST_COMPLETED)
        
        if self._reader_task in done:
            self._reader_task = asyncio.create_task(self._reader_coro())
        if self._writer_task in done:
            self._writer_task = asyncio.create_task(self._writer_coro())

    async def _reader_coro(self):
        data = await self.read_message()
        if not data:
            self._leave = True
            return

        self.dispatcher.call_handlers_for_packet(data, self.peername)
    
    async def _writer_coro(self):
        data = await self._to_write.get()
        try:
            self.writer.write(data)
            await self.writer.drain()
        except (BrokenPipeError,
                TimeoutError,
                ConnectionResetError) as e:
            logging.info(f"Can't write to {self}, the connection is probably gone.")
            self._leave = True
        except Exception as e:
            logging.exception("Exception when writing back..")
            self._leave = True

    async def join(self):
        self.add_route_map()
        self.user.group.users.notification_callbacks.append(self.send_user_list)
        self.user.group.users.notify_cbs()

        while True and self.on:
            await self.process_messages()
            last_alive = time.time()

        self.user.group.unregister(self)       
        self.user.connections.remove(self)
        self.user.group.users.notify_cbs()
        self.user.group.users.notification_callbacks.remove(self.send_user_list)

        await self.close()

    def add_route_map(self):
        self.dispatcher.map('*', self.user.route)

    def send_user_list(self, users):
        self.send_message('/oscrouter/userlist', *[user.name for user in users])

    def send_message(self, address, *args):
        msg = OscMessageBuilder(address)
        for arg in args:
            msg.add_arg(arg)
        data = msg.build().dgram
        length = len(data)
        data = struct.pack('>i', length) + data
        self._to_write.put_nowait(data)


class UserRegistry:
    def __init__(self, group):
        self.by_name: Dict[str, User] = {}
        self.by_connection: Dict[Connection, User] = {}
        self.notification_callbacks = []
        self._group = group

    def __str__(self):
        return f"UserRegistry[{self._group}]"

    def update(self, user):
        new_user = False
        if user.name not in self.by_name.keys():
            self.by_name[user.name] = user
            new_user = True

        for conn in user.connections:
            self.by_connection[conn] = user

        if new_user:
            logging.info(f"New user '{user}' registered in '{self}'")
        else:
            logging.info(f"User '{user}' updated in '{self}'")
        self.notify_cbs()

    def notify_cbs(self):
        for cb in self.notification_callbacks:
            cb([ user for user in self.by_name.values()])

    def unregister(self, user):
        del self.by_name[user.name]
        for conn in user.connections:
            del self.by_connection[conn]
        self.notify_cbs()

    def __len__(self):
        return len(self.by_name.keys())

    def all(self):
        return self.by_name.values()


class Group:
    name: str
    password: str
    users: UserRegistry
    
    index = {}

    def __init__(self, name: str, password: str):
        self.name = name
        self.password = password
        self.users = UserRegistry(self)

    def __str__(self):
        return self.name

    def unregister(self, connection):
        if len(connection.user.connections) <= 1:
            self.users.unregister(connection.user)
        else: 
            del self.users.by_connection[connection]
 
        if len(self.users) == 0:
            logging.info(f"Group '{self}' is empty, deleting it.")
            self.close()

    def auth(self, name, password):
        if self.name == name and self.password == password:
            Group.index[self.name] = self
            return True
        return False

    def close(self):
        del Group.index[self.name]


class User:
    name: str
    password: str
    group: Optional[Group]
    connections: List[Connection]

    def __init__(self):
        self.name = ""
        self.password = ""
        self.group = None
        self.connections = []

    def __str__(self):
        return f"{self.name}({self.group})[{len(self.connections)}]"

    @property
    def authenticated(self):
        return self.name != "" and self.password != ""

    def auth(self, name, password):
        if self.name == "" and self.password == "":
            logging.info(f"Creating new user with name '{name}' in group '{self.group}'")
            self.name = name
            self.password = password
            return True

        if self.name != name or self.password != password:
            logging.error(f"User '{self.name}' failed to authenticate in group '{self.group}'.")
            return False

        logging.info(f"User '{self}' authenticated.")
        return True

    def send_message(self, address, *args):
        for connection in self.connections:
            connection.send_message(address, *args)

    def route(self, address, *args):
        if address ==  "/oscrouter/ping":
            return
        if address == "/oscrouter/private":
            if len(args) >= 1:
                username = args[0]
                user = self.group.users.by_name.get(username, None)
                if user:
                    logging.info(f"-> sending message '{args[1]}' with args: '{args[2:]}' from '{self}' to {user}")
                    user.send_message("/oscrouter/private", self.name, *args[1:])
            return

        logging.info(f"-> routing message '{address}' with args: '{args}' from '{self}'")
        for user in self.group.users.by_name.values():
            if user is self:
                continue
            user.send_message(address, *args)


async def handle_new_conn(reader, writer):
    connection = Connection(reader, writer)
    await connection.try_register()

    if connection.user and connection.user.authenticated:
        await connection.join()

    await connection.close()

    logging.info(f"{connection} closed")
