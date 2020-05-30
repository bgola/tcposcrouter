import logging
import logging.handlers

warning_handler = logging.StreamHandler()
warning_handler.setLevel(logging.WARNING)

handler = logging.handlers.RotatingFileHandler("router.log",  mode='a', maxBytes=1024*1024, backupCount=10)
logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO, handlers=[handler, warning_handler])

# OSC

OSC_PORT = 55555

# WebSocket

WEBSOCKET_PORT = 5681
SSL = False

## If using SSL for the websocket:
PEM = "/path/to/fullchain.pem"
PVK = "/path/to/privkey.pem"
