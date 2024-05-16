import enum
import logging
import struct
from datetime import datetime, timedelta
from typing import BinaryIO

logger = logging.getLogger(__name__)


class KngKmall:
    class Flags(enum.Enum):
        VALID = 0
        UNEXPECTED_EOF = 1
        CORRUPTED_END_DATAGRAM = 2

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.length = None
        self.id = None
        self.version = None
        self.system_id = None
        self.sounder_id = None
        self.time_sec = None
        self.time_nanosec = None
        self.dg_time = None

    def read(self, file_input: BinaryIO, file_size: int) -> Flags:
        """populate header data"""

        chunk = file_input.read(20)
        hdr_data = struct.unpack("<I4cBBHII", chunk)

        self.length = hdr_data[0]
        # logger.debug('length: %s' % self.length)
        self.id = b''.join(hdr_data[1:5])
        # logger.debug('type: %s -> %s' % (self.type, self.kmall_datagrams[self.type]))
        self.version = hdr_data[5]
        # logger.debug('version: %s' % self.version)
        self.system_id = hdr_data[6]
        # logger.debug('system id: %s' % self.system_id)
        self.sounder_id = hdr_data[7]
        # logger.debug('sounder id: %s' % self.sounder_id)
        self.time_sec = hdr_data[8]
        # logger.debug('time sec: %s' % self.time_sec)
        self.time_nanosec = hdr_data[9]
        # logger.debug('time nanosec: %s' % self.time_nanosec)
        self.dg_time = self.kmall_datetime(self.time_sec, self.time_nanosec)
        # logger.debug('datetime: %s' % self.dg_time.strftime('%Y-%m-%d %H:%M:%S.%f'))

        # try to read ETX

        # Make sure we don't try to read beyond the EOF (-13 since 16 for header and 3 for ender)
        if (file_input.tell() + (self.length - 20)) >= file_size:
            if self.verbose:
                logger.warning("unexpected EOF > current pos: %s, datagram length: %s, file size: %s"
                               % (file_input.tell(), self.length, file_size))
            return self.Flags.UNEXPECTED_EOF

        # move file cursor to the end of the datagram
        file_input.seek(self.length - 24, 1)

        chunk = file_input.read(4)
        footer_length = struct.unpack("<I", chunk)[0]

        if footer_length != self.length:
            logger.info("datagram length mismatch: %s vs. %s" % (self.length, footer_length))

            return self.Flags.CORRUPTED_END_DATAGRAM

        return self.Flags.VALID

    @classmethod
    def kmall_datetime(cls, dgm_time_sec: int, dgm_time_nanosec: int = 0):
        return datetime.utcfromtimestamp(dgm_time_sec) + \
               timedelta(microseconds=(dgm_time_nanosec / 1000.0))
