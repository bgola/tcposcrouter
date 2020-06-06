import argparse
import asyncio
import logging
import websockets
import os
import logging
import logging.handlers

from tcposcrouter.router import handle_new_conn, handle_websocket


async def run_server(osc_port, websocket_port, log_dir, fullchain_pem, private_key):
    warning_handler = logging.StreamHandler()
    warning_handler.setLevel(logging.WARNING)

    handler = logging.handlers.RotatingFileHandler(os.path.join(log_dir, 'tcposcrouter.log') ,  mode='a', maxBytes=1024**4, backupCount=10)
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO, handlers=[handler, warning_handler])

    loop = asyncio.get_event_loop()
    server = await asyncio.start_server(
        handle_new_conn, '0.0.0.0', osc_port)

    addr = server.sockets[0].getsockname()
    logging.warning(f'Serving on {addr}')

    if fullchain_pem and private_key:
        import ssl
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(fullchain_pem, private_key)
        ws_server = await websockets.serve(handle_websocket, '0.0.0.0', websocket_port, ssl=ssl_context, max_size=None)
    else:
        ws_server = await websockets.serve(handle_websocket, '0.0.0.0', websocket_port)

    async with server:
        await asyncio.gather(server.serve_forever(), ws_server.server.serve_forever())


def main():
    parser = argparse.ArgumentParser(description='Run the tcposcrouter server.')
    parser.add_argument('--osc-port', help='OSC port to listen', default=55555)
    parser.add_argument('--websocket-port', help='WebSocket port to listen', default=5681)
    parser.add_argument('--log-dir', help='Path where to save logs', default='.')
    parser.add_argument('--fullchain-pem', help='Path to SSL fullchain.pem (if using SSL for the websocket)')
    parser.add_argument('--private-key', help='Path to SSL privkey.pem (if using SSL for the websocket)')

    args = parser.parse_args()
    asyncio.run(run_server(args.osc_port, args.websocket_port, args.log_dir, args.fullchain_pem, args.private_key))

if __name__ == "__main__":
    main()
