import datetime
import time
import threading
import socket
import struct
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SvpThread(threading.Thread):

    class Sis:
        def __init__(self):
            self.installation = list()
            self.runtime = list()
            self.ssp = list()
            self.lists_lock = threading.Lock()

            self.r20_count = 0
            self.ssp_count = 0
            self.snn_count = 0

    def __init__(self, installation: list, runtime: list, ssp: list, lists_lock: threading.Lock,
                 port_in: int = 4001, port_out: int = 26103, ip_out: str = "localhost",
                 target: Optional[object] = None, name: str = "SVP", use_sis5: bool = False,
                 debug: bool = False) -> None:
        threading.Thread.__init__(self, target=target, name=name)
        self.debug = debug

        self.port_in = port_in
        self.port_out = port_out
        self.ip_out = ip_out
        self.use_sis5 = use_sis5

        self.sock_in = None
        self.sock_out = None

        self.sis = SvpThread.Sis()
        self.sis.installation = installation
        self.sis.runtime = runtime
        self.sis.ssp = ssp
        self.sis.lists_lock = lists_lock

        self.shutdown = threading.Event()

    def _close_sockets(self) -> None:
        if self.sock_in:
            self.sock_in.close()
            self.sock_in = None
        if self.sock_out:
            self.sock_out.close()
            self.sock_out = None

    def run(self) -> None:
        logger.debug("%s started -> in %s, out %s:%s" % (self.name, self.port_in, self.ip_out, self.port_out))
        self.init_sockets()
        while True:
            if self.shutdown.is_set():
                self._close_sockets()
                break
            self.interaction()
            time.sleep(1)

        logger.debug("%s end" % self.name)

    def stop(self) -> None:
        """Stop the thread"""
        self.shutdown.set()

    def init_sockets(self) -> None:
        """Initialize UDP sockets"""

        self.sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_in.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock_in.settimeout(10)
        self.sock_in.bind(("0.0.0.0", self.port_in))

        self.sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_out.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2 ** 16)
        if self.debug:
            logger.debug("sock_out > buffer %sKB" %
                         (self.sock_out.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF) / 1024))

    def interaction(self) -> None:
        try:
            data, address = self.sock_in.recvfrom(2 ** 16)  # 2**15 is max UDP datagram size
            data = data.decode('utf-8')

        except socket.timeout:
            logger.debug("sleep")
            time.sleep(0.1)
            return

        logger.debug("msg from %s [sz: %sB]" % (address, len(data)))
        if len(data) < 6:
            logger.debug("Too short data: %s" % data)
            return
        if self.debug:
            logger.debug("received: %s" % data)

        if self.use_sis5:
            self._sis_5(data)
        else:
            self._sis_4(data)

    def _sis_5(self, data) -> None:
        if data[0:4] == "$MVS":
            # the big assumption here is that we have received a valid Snn profile

            if isinstance(data, bytes):
                data = data.decode("utf-8")

            if self.debug and (len(data) > 8):
                logger.debug("received %s" % data[:6])
            # logger.debug("received data:\n%s" % data)
            self.sis.snn_count += 1

            self.send_received_profile(data)

        else:
            logger.warning('Received unknown message: %s' % data[:9])

    def _sis_4(self, data) -> None:

        if data[0] == '$' and data[3:6] == "R20":

            if self.debug:
                logger.debug("got IUR request!")
            self.sis.r20_count += 1

            if len(self.sis.ssp) == 0:
                self.send_fake_profile()
                return

            self.send_latest_received_profile()
            return

        elif data[0:4] == "$MVS":
            # the big assumption here is that we have received a valid Snn profile

            if isinstance(data, bytes):
                data = data.decode("utf-8")

            if self.debug and (len(data) > 8):
                logger.debug("received %s" % data[:6])
            # logger.debug("received data:\n%s" % data)
            self.sis.snn_count += 1

            self.send_received_profile(data)

        else:
            logger.warning('Received unknown message: %s' % data[:9])

    def send_fake_profile(self):
        date = None
        secs = None

        # If we're running but haven't received an SVP yet, then we build a fake one to send back.
        # Useful in testing the Server mode since the library establishes comm's before starting to serve
        num_entries = 8
        depths = np.zeros(num_entries)
        speeds = np.zeros(num_entries)
        depths[0] = 0.0
        speeds[0] = 1537.63
        depths[1] = 50.0
        speeds[1] = 1537.52
        depths[2] = 100.0
        speeds[2] = 1529.96
        depths[3] = 300.0
        speeds[3] = 1521.80
        depths[4] = 800.0
        speeds[4] = 1486.73
        depths[5] = 1400.0
        speeds[5] = 1444.99
        depths[6] = 1600.0
        speeds[6] = 1447.25
        depths[7] = 12000.0
        speeds[7] = 1500.0
        if self.debug:
            logger.debug("made up a fake profile")  # it will send at the end of the function

        if self.use_sis5:
            ssp = self._create_sis5_ssp(depths=depths, speeds=speeds, date=date, secs=secs)
        else:
            ssp = self._create_sis4_ssp(depths=depths, speeds=speeds, date=date, secs=secs)
        if self.debug:
            logger.debug("sending data: %s" % repr(ssp))
        time.sleep(1.5)
        self.sock_out.sendto(ssp, (self.ip_out, self.port_out))
        with self.sis.lists_lock:
            self.sis.ssp.append(ssp)
        if self.debug:
            logger.debug("data sent")
        self.sis.ssp_count += 1

    def send_latest_received_profile(self):
        with self.sis.lists_lock:

            # First send the Installation parameters
            if self.debug:
                logger.debug("installation datagrams: %d" % len(self.sis.installation))
            if len(self.sis.installation) != 0:
                installation = self.sis.installation[-1]
                if self.debug:
                    logger.debug("sending installation: %s" % self.sis.installation)
                self.sock_out.sendto(installation, (self.ip_out, self.port_out))
                time.sleep(0.5)

            # Second send the Runtime parameters
            if self.debug:
                logger.debug("runtime datagrams: %d" % len(self.sis.runtime))
            if len(self.sis.runtime) != 0:
                runtime = self.sis.runtime[-1]
                if self.debug:
                    logger.debug("sending runtime: %s" % self.sis.runtime)
                self.sock_out.sendto(runtime, (self.ip_out, self.port_out))
                time.sleep(0.5)

            # Third send the SVP ...
            if self.debug:
                logger.debug("ssp datagrams: %d" % len(self.sis.ssp))
            if len(self.sis.ssp) != 0:

                if self.debug:
                    logger.debug("sending svp")

                time.sleep(1.5)
                ssp = self.sis.ssp[-1]
                self.sock_out.sendto(ssp, (self.ip_out, self.port_out))
                self.sis.ssp_count += 1
                return
            else:
                logger.warning('No profiles received. Try again!')

    def send_received_profile(self, data):
        date = None
        secs = None
        depths = None
        speeds = None
        count = 0
        header = False

        for row in data.splitlines():

            if count == 0:  # first line
                if "CALC" in row:
                    logger.warning("HYPACK profile")
                    return

            num_fields = len(row.split(","))
            if num_fields == 12:  # header

                fields = row.split(",")
                num_entries = int(fields[2])
                timestamp = datetime.datetime.strptime(fields[3], "%H%M%S")
                secs = (timestamp - timestamp.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
                datestamp = datetime.datetime(day=int(fields[4]), month=int(fields[5]), year=int(fields[6]))
                date = int(datestamp.strftime("%Y%m%d"))
                depths = np.zeros(num_entries)
                speeds = np.zeros(num_entries)
                depths[count] = fields[7]
                speeds[count] = fields[8]
                header = True

            elif num_fields == 5:

                if not header:
                    logger.warning("unable to parse received header")
                    return
                depths[count] = row.split(",")[0]
                speeds[count] = row.split(",")[1]

            count += 1

        if self.use_sis5:
            ssp = self._create_sis5_ssp(depths=depths, speeds=speeds, date=date, secs=secs)
        else:
            ssp = self._create_sis4_ssp(depths=depths, speeds=speeds, date=date, secs=secs)
        if self.debug:
            logger.debug("sending data: %s" % repr(ssp))
        time.sleep(1.5)
        self.sock_out.sendto(ssp, (self.ip_out, self.port_out))
        with self.sis.lists_lock:
            self.sis.ssp.append(ssp)
        if self.debug:
            logger.debug("data sent")
        self.sis.ssp_count += 1

    def _create_sis5_ssp(self, depths: np.ndarray, speeds: np.ndarray,
                         date: Optional[int] = None, secs: Optional[int] = None) -> bytes:
        if self.debug:
            logger.debug('creating a SIS5 binary ssp')

        common_hdr_fmt = "<I4cBBHII"
        dg_hdr_fmt = "<2H4BIdd"
        dg_pnt_fmt = "<2fI2f"
        common_ftr_fmt = "<I"

        dg_date = 334582200
        if date:
            try:
                date_object = datetime.datetime.strptime(date, "%Y%m%d")
                dg_date = int(date_object.timestamp())
                if secs:
                    dg_date += secs
            except Exception as e:
                logger.warning('Unable to interpret the timestamp: %s and %s -> %s'
                               % (date, secs, e))

        dg_length = struct.calcsize(common_hdr_fmt) + struct.calcsize(dg_hdr_fmt) + \
                    depths.size * struct.calcsize(dg_pnt_fmt) + struct.calcsize(common_ftr_fmt)

        # -- header                        length,       datagram id,
        svp = struct.pack(common_hdr_fmt, dg_length, b'#', b'S', b'V', b'P',
                          # version, system id, echosounder id, time sec, nanosec
                          1, 1, 302, dg_date, 0)

        # logger.debug("%s, %s, %s" % (type(struct.calcsize(dg_hdr_fmt)), type(int(depths.size)), type(dg_date)))
        # -- dg header                      bytes common part,      nr samples,      sensor format,
        svp += struct.pack(dg_hdr_fmt, struct.calcsize(dg_hdr_fmt), int(depths.size),
                           ord('S'), ord('0'), ord('0'), ord(' '),
                           # time sec, latitude, longitude
                           dg_date, 43.13555, -70.9395
                           )

        # -- dg points
        for count in range(depths.size):
            #                              depth,         sound speed, pad, temp, sal
            svp += struct.pack(dg_pnt_fmt, depths[count], speeds[count], 0, 0.0, 0.0)

        # -- footer
        svp += struct.pack(common_ftr_fmt, dg_length)

        return svp

    def _create_sis4_ssp(self, depths: np.ndarray, speeds: np.ndarray,
                         date: Optional[int] = None, secs: Optional[int] = None) -> bytes:
        if self.debug:
            logger.debug('creating a SIS4 binary ssp')

        d_res = 1  # depth resolution
        # TODO: improve it with the received metadata
        now = datetime.datetime.utcnow()
        if not date:
            date = int(now.strftime("%Y%m%d"))
        if not isinstance(date, int):
            date = int(date)
        if not secs:
            secs = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        if not isinstance(secs, int):
            secs = int(secs)

        # -- header
        # logger.debug("types: %s %s %s %s" % (type(date), type(secs), type(depths.size), type(d_res)))
        svp = struct.pack("<BBHIIHHIIHH", 2, 0x55, 122, date, secs * 1000, 1, 123, date, secs, depths.size, d_res)

        # -- body
        for count in range(depths.size):
            depth = int(depths[count] * d_res / 0.01)
            speed = int(speeds[count] * 10)
            pair = struct.pack("<II", depth, speed)
            svp += pair

        # -- footer
        footer = struct.pack("<BH", 3, 0)  # Not bothering with checksum since SVP Editor ignores it anyway
        svp += footer

        return svp

    def info(self) -> str:
        msg = "Received Datagrams:\n"
        msg += "- R20: %d\n" % self.sis.r20_count
        msg += "- Snn: %d\n" % self.sis.snn_count
        msg += "Reacted Datagrams:\n"
        msg += "- ssp: %d\n" % self.sis.ssp_count
        return msg
