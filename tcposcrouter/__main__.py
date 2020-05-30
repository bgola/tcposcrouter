import settings
import asyncio
import logging
import websockets

from router import handle_new_conn, handle_websocket


async def run_server():
    loop = asyncio.get_event_loop()
    server = await asyncio.start_server(
        handle_new_conn, '0.0.0.0', settings.OSC_PORT)

    addr = server.sockets[0].getsockname()
    logging.warning(f'Serving on {addr}')

    if settings.SSL:
        import ssl
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(settings.PEM, settings.PVK)
        ws_server = await websockets.serve(handle_websocket, '0.0.0.0', settings.WEBSOCKET_PORT, ssl=ssl_context, max_size=None)
    else:
        ws_server = await websockets.serve(handle_websocket, '0.0.0.0', settings.WEBSOCKET_PORT)

    async with server:
        await asyncio.gather(server.serve_forever(), ws_server.server.serve_forever())


def main():
    asyncio.run(run_server())

if __name__ == "__main__":
    main()
