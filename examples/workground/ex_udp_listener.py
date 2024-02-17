import logging
import socket

from hyo2.abc2.lib.logging import set_logging

logger = logging.getLogger(__name__)
set_logging()

ip = '127.0.0.1'
port = 14001

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((ip, port))

# Receive/respond loop
while True:

    logger.debug('waiting to receive message ...')
    data, address = sock.recvfrom(2 ** 16)  # 2**15 is max UDP datagram size
    logger.debug('rx: %s' % data)
