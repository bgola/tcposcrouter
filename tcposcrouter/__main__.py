import argparse
import asyncio
import logging
import os
import logging
import logging.handlers

from tcposcrouter.router import handle_new_conn


async def run_server(osc_port_10, osc_port_11, log_dir, disable_osc10, disable_osc11):
    warning_handler = logging.StreamHandler()
    warning_handler.setLevel(logging.WARNING)

    handler = logging.handlers.RotatingFileHandler(os.path.join(log_dir, 'tcposcrouter.log') ,  mode='a', maxBytes=1024**4, backupCount=10)
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO, handlers=[handler, warning_handler])

    loop = asyncio.get_event_loop()

    servers = []

    if not disable_osc10:
        server10 = await asyncio.start_server(
            handle_new_conn(1.0), '0.0.0.0', osc_port_10)
        servers.append(server10.serve_forever())
        addr = server10.sockets[0].getsockname()
        logging.warning(f'Serving OSC spec-1.0 on {addr}')

    if not disable_osc11:
        server11 = await asyncio.start_server(
            handle_new_conn(1.1), '0.0.0.0', osc_port_11)
        servers.append(server11.serve_forever())
        addr = server11.sockets[0].getsockname()
        logging.warning(f'Serving OSC spec-1.1 on {addr}')

    await asyncio.gather(*servers)


def main():
    parser = argparse.ArgumentParser(description='Run the tcposcrouter server.')
    parser.add_argument('--osc-port', help='OSC port to listen', default=55555)
    parser.add_argument('--osc11-port', help='OSC port to listen using SLIP encoding', default=55556)
    parser.add_argument('--disable-osc10', help='Disables data length prefix (OSC spec-1.0)', default=False, action='count')
    parser.add_argument('--disable-osc11', help='Disables SLIP encoding (OSC spec-1.1)', default=False, action='count')
    parser.add_argument('--log-dir', help='Path where to save logs', default='.')

    args = parser.parse_args()
    
    if args.disable_osc10 and args.disable_osc11: 
        logging.warning("Both OSC specs 1.0 and 1.1 are disabled, nothing to do.")
        return 

    asyncio.run(run_server(args.osc_port, args.osc11_port, args.log_dir, args.disable_osc10, args.disable_osc11))

if __name__ == "__main__":
    main()
