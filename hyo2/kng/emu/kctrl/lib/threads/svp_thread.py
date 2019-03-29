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
    def __init__(self, installation: list, runtime: list, ssp: list, lists_lock: threading.Lock,
                 port_in: int = 6020, port_out: int = 26103, ip_out: str = "224.1.20.40",
                 target: Optional[object] = None, name: str = "SVP",
                 verbose: bool = False) -> None:
        threading.Thread.__init__(self, target=target, name=name)
        self.verbose = verbose

        self.port_in = port_in
        self.port_out = port_out
        self.ip_out = ip_out

        self.sock_in = None
        self.sock_out = None

        self.installation = installation
        self.runtime = runtime
        self.ssp = ssp
        self.lists_lock = lists_lock

        self.shutdown = threading.Event()

    def _close_sockets(self):
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

        # # Tell the operating system to add the socket to
        # # the multicast group on all interfaces.
        # group = socket.inet_aton(self.ip_out)
        # mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        # self.sock_in.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self.sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_out.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2 ** 16)
        # allow reuse of addresses
        self.sock_out.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Messages time-to-live to 1 to avoid forwarding beyond current network segment.
        ttl = struct.pack('b', 1)  # TODO: How does K-Controller control this?
        self.sock_out.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

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
        logger.debug("received: %s" % data)

        ssp = self._sis_5(data)

        if ssp:
            if self.verbose:
                logger.debug("sending data: %s" % repr(ssp))
            time.sleep(1.5)

            self.sock_out.sendto(ssp, (self.ip_out, self.port_out))
            with self.lists_lock:
                self.ssp.append(ssp)

            if self.verbose:
                logger.debug("data sent")

    def _sis_5(self, data):
        secs = None

        if data[0] == '$' and data[3:6] == "R20":

            logger.debug("got IUR request!")

            with self.lists_lock:

                # First send the Installation parameters
                logger.debug("installation datagrams: %d" % len(self.installation))
                if len(self.installation) != 0:
                    installation = self.installation[-1]
                    if self.verbose:
                        logger.debug("sending installation: %s" % self.installation)
                    self.sock_out.sendto(installation, (self.ip_out, self.port_out))
                    time.sleep(0.5)

                # Second send the Runtime parameters
                logger.debug("runtime datagrams: %d" % len(self.runtime))
                if len(self.runtime) != 0:
                    runtime = self.runtime[-1]
                    if self.verbose:
                        logger.debug("sending runtime: %s" % self.runtime)
                    self.sock_out.sendto(runtime, (self.ip_out, self.port_out))
                    time.sleep(0.5)

                # Third send the SVP ...
                logger.debug("ssp datagrams: %d" % len(self.ssp))
                if len(self.ssp) != 0:

                    if self.verbose:
                        logger.debug("sending svp")

                    time.sleep(1.5)
                    ssp = self.ssp[-1]
                    self.sock_out.sendto(ssp, (self.ip_out, self.port_out))
                    return

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
            if self.verbose:
                logger.debug("making up a fake profile")  # it will send at the end of the function

        else:
            # the big assumption here is that we received a valid Snn profile

            if isinstance(data, bytes):
                data = data.decode("utf-8")

            if self.verbose and (len(data) > 8):
                logger.debug("received %s[...]" % data[:6])

            depths = None
            speeds = None
            count = 0
            header = False

            for l in data.splitlines():

                if count == 0:  # first line
                    if "CALC" in l:
                        logger.warning("HYPACK profile")
                        return

                num_fields = len(l.split(","))
                if num_fields == 12:  # header

                    fields = l.split(",")
                    num_entries = int(fields[2])
                    timedelta = datetime.datetime.strptime(fields[3], "%H%M%S") - \
                                datetime.datetime.strptime("000000", "%H%M%S")
                    datestamp = datetime.datetime(day=int(fields[4]), month=int(fields[5]), year=int(fields[6]))
                    secs = (datestamp + timedelta - datetime.datetime(1970, 1, 1)).total_seconds()
                    depths = np.zeros(num_entries)
                    speeds = np.zeros(num_entries)
                    depths[count] = fields[7]
                    speeds[count] = fields[8]
                    header = True

                elif num_fields == 5:

                    if not header:
                        logger.warning("unable to parse received header")
                        return
                    depths[count] = l.split(",")[0]
                    speeds[count] = l.split(",")[1]

                count += 1

        ssp = self._create_all_ssp(depths=depths, speeds=speeds, secs=secs)
        return ssp

    def _create_all_ssp(self, depths: np.ndarray, speeds: np.ndarray, secs: Optional[int] = None):
        if self.verbose:
            logger.debug('creating a binary svp')

        d_res = 1  # depth resolution
        # TODO: improve it with the received metadata
        now = datetime.datetime.utcnow()
        if not secs:
            secs = (now - datetime.datetime(1970, 1, 1)).total_seconds()
        if not isinstance(secs, int):
            secs = int(secs)

        header_struct = '<I4cBBHII'
        header_size = struct.calcsize(header_struct)
        svp_struct = '<2H4cIdd'
        svp_size = struct.calcsize(svp_struct)
        fields_struct = '<2fI2f'
        fields_size = struct.calcsize(fields_struct)
        end_struct = '<H'
        end_size = struct.calcsize(end_struct)

        total_svp_size = svp_size + fields_size * depths.size
        total_size = header_size + total_svp_size + end_size

        # -- header
        svp = struct.pack(header_struct, total_size, b'#', b'S', b'V', b'P', 0, 0, 0, 0, 0)

        # -- svp
        logger.debug("secs: %s" % (secs, ))
        svp += struct.pack('<2H4cI', total_svp_size, depths.size, b' ', b'S', b'0', b'0', secs)
        svp += struct.pack('<dd', 43.1355, -70.9395)

        # -- body
        for count in range(depths.size):
            depth = depths[count]
            speed = speeds[count]
            pair = struct.pack(fields_struct, depth, speed, 0, 0.0, 0.0)
            svp += pair

        # -- footer
        svp += struct.pack(end_struct, total_size)

        return svp
