import argparse
import asyncio
import logging
import os
import logging
import logging.handlers

from tcposcrouter.router import handle_new_conn


async def run_server(osc_port, log_dir):
    warning_handler = logging.StreamHandler()
    warning_handler.setLevel(logging.WARNING)

    handler = logging.handlers.RotatingFileHandler(os.path.join(log_dir, 'tcposcrouter.log') ,  mode='a', maxBytes=1024**4, backupCount=10)
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO, handlers=[handler, warning_handler])

    loop = asyncio.get_event_loop()
    server = await asyncio.start_server(
        handle_new_conn, '0.0.0.0', osc_port)

    addr = server.sockets[0].getsockname()
    logging.warning(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description='Run the tcposcrouter server.')
    parser.add_argument('--osc-port', help='OSC port to listen', default=55555)
    parser.add_argument('--log-dir', help='Path where to save logs', default='.')

    args = parser.parse_args()
    asyncio.run(run_server(args.osc_port, args.log_dir))

if __name__ == "__main__":
    main()
