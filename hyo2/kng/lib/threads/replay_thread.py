import logging
import os
import socket
import threading
import time
from threading import Lock
from typing import List, Optional

from hyo2.kng.lib.kng_all import KngAll
from hyo2.kng.lib.kng_kmall import KngKmall

logger = logging.getLogger(__name__)


class ReplayThread(threading.Thread):
    """Mimic the interaction with a real SIS

    To check who is listening on port 4001: netstat -a -n -o | find "4001"
    then to know the process name: tasklist /fi "pid eq 2216"
    """

    class Sis:
        def __init__(self):
            self.installation = list()  # type: List[bytes]
            self.runtime = list()  # type: List[bytes]
            self.ssp = list()  # type: List[bytes]
            self.lists_lock = threading.Lock()

    class Sis4:
        def __init__(self):
            self.surface_ssp_count = 0
            self.nav_count = 0
            self.installation_count = 0
            self.runtime_count = 0
            self.ssp_count = 0
            self.svp_input_count = 0
            self.xyz88_count = 0
            self.range_angle78_count = 0
            self.seabed_image89_count = 0
            self.watercolumn_count = 0
            self.bist_count = 0

    class Sis5:
        def __init__(self):
            self.iip_count = 0  # Installation parameters and sensor setup datagram
            self.iop_count = 0  # Runtime parameters as chosen by operator datagram
            self.mrz_count = 0  # Multibeam (M) raw range (R) and depth(Z) datagram
            self.spo_count = 0  # Sensor (S) data for position (PO) datagram
            self.ssm_count = 0  # Sound Speed Manager (SSM) datagram
            self.svp_count = 0  # Sensor (S) data from sound velocity (V) profile (P) or CTD datagram

    def __init__(self, installation: List[bytes], runtime: List[bytes], ssp: List[bytes], lists_lock: threading.Lock,
                 files: List[str], replay_timing: float = 1.0, port_out: int = 26103,
                 ip_out: str = "localhost", target: Optional[object] = None, name: str = "REP", use_sis5: bool = False,
                 debug: bool = False, replay_ssm: bool = True, replay_mrz: bool = True):
        threading.Thread.__init__(self, target=target, name=name)
        self.debug = debug

        self.port_out = port_out
        self.ip_out = ip_out
        self.use_sis5 = use_sis5
        self._replay_ssm = replay_ssm
        self._replay_mrz = replay_mrz
        self._replay_timing = replay_timing
        self.files = files

        self.sock_in = None
        self.sock_out = None

        self.sis = ReplayThread.Sis()
        self.sis.installation = installation
        self.sis.runtime = runtime
        self.sis.ssp = ssp
        self.sis.lists_lock = lists_lock

        self.sis4 = ReplayThread.Sis4()
        self.sis5 = ReplayThread.Sis5()

        self.dg_counter = None

        self.shutdown = threading.Event()
        self._lock = Lock()
        self._external_lock = False

    @property
    def replay_timing(self):
        if not self._external_lock:
            raise RuntimeError("Accessing resources without locking them!")
        return self._replay_timing

    @replay_timing.setter
    def replay_timing(self, value):
        if not self._external_lock:
            raise RuntimeError("Modifying resources without locking them!")
        self._replay_timing = value

    def lock_data(self):
        self._lock.acquire()
        self._external_lock = True

    def unlock_data(self):
        self._lock.release()
        self._external_lock = False

    def _close_sockets(self):
        if self.sock_in:
            self.sock_in.close()
            self.sock_in = None
        if self.sock_out:
            self.sock_out.close()
            self.sock_out = None

    def run(self):
        logger.debug("%s started -> out %s:%s, timing: %s"
                     % (self.name, self.ip_out, self.port_out, self._replay_timing))

        self.init_sockets()
        while True:
            if self.shutdown.is_set():
                self._close_sockets()
                break
            self.interaction()
            time.sleep(1)
            logger.debug("sleep")

        logger.debug("%s ends" % self.name)

    def stop(self):
        """Stop the thread"""
        self.shutdown.set()

    def init_sockets(self):
        """Initialize UDP sockets"""

        self.sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_out.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2 ** 16)

        logger.debug("sock_out > buffer %sKB" %
                     (self.sock_out.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF) / 1024))

    def interaction(self):
        # logger.debug("reading files")

        self.dg_counter = 0

        for fp in self.files:
            if self.shutdown.is_set():
                self._close_sockets()
                break

            fp_ext = os.path.splitext(fp)[-1].lower()
            if self.use_sis5:
                if fp_ext not in [".kmall"]:
                    logger.info("SIS 5 mode -> skipping unsupported file extension: %s" % fp)
                    continue
            else:
                if fp_ext not in [".all", ".wcd"]:
                    logger.info("SIS 4 mode -> skipping unsupported file extension: %s" % fp)
                    continue

            try:
                f = open(fp, 'rb')
                f_sz = os.path.getsize(fp)

            except (OSError, IOError):
                raise RuntimeError("unable to open %s" % fp)

            logger.debug("open file: %s [%iKB]" % (fp, (f_sz / 1024)))

            while True:

                if self.shutdown.is_set():
                    self._close_sockets()
                    break

                if self.use_sis5:
                    break_loop = self._sis_5(f, f_sz)
                else:
                    break_loop = self._sis_4(f, f_sz)
                if break_loop:
                    break

                if f.tell() >= f_sz:
                    # end of file
                    logger.debug("EOF")
                    break

            f.close()
            if self.debug:
                logger.debug("data loaded > datagrams: %s" % self.dg_counter)
            self.files.append(fp)

    def _sis_5(self, f, f_sz) -> bool:
        # guardian to avoid to read beyond the EOF
        if (f.tell() + 16) > f_sz:
            if self.debug:
                logger.debug("EOF")
            return True

        base = KngKmall(verbose=True)
        ret = base.read(f, f_sz)
        # logger.info(ret)
        if ret == KngKmall.Flags.UNEXPECTED_EOF:

            logger.warning("troubles in reading file > SKIP (reason: unexpected EOF)")
            return True

        elif ret == KngKmall.Flags.CORRUPTED_END_DATAGRAM:

            f.seek(-(base.length + 3), 1)
            logger.warning("troubles in reading final datagram part > REALIGN to position: %s" % f.tell())

        elif ret == KngKmall.Flags.VALID:

            self.dg_counter += 1

        else:
            raise RuntimeError("unknown return %s from KngKmall" % ret)

        # Read and send only the desired datagrams:
        # - b'#IIP': 'Installation parameters and sensor setup'
        # - b'#IOP': 'Runtime parameters as chosen by operator'
        # - b'#SPO': 'Sensor (S) data for position (PO)'
        # - b'#MRZ': 'Multibeam (M) raw range (R) and depth(Z) datagram'
        # - b'#SVP': 'Sensor (S) data from sound velocity (V) profile (P) or CTD'
        # - b'#SSM': 'Sound (S) Speed (S) Manager (M)'
        filtered_datagrams = [b'#IIP', b'#IOP', b'#SVP']
        if self._replay_mrz:
            filtered_datagrams.append(b'#SPO')
            filtered_datagrams.append(b'#MRZ')
        if self._replay_ssm:
            filtered_datagrams.append(b'#SSM')
        if base.id not in filtered_datagrams:
            return False

        if base.length > 65507:
            logger.info("%s > skipping dg %s (length: %sB) > datagram split not implemented"
                        % (base.dg_time, base.id, base.length))
            return False

        logger.debug("%s > sending dg %s (length: %sB)" % (base.dg_time, base.id, base.length))
        f.seek(-base.length, 1)
        dg_data = f.read(base.length)

        # Stores a few datagrams of interest in data lists:
        with self.sis.lists_lock:
            if base.id == b'#IIP':
                self.sis.installation.clear()
                self.sis.installation.append(dg_data)
                self.sis5.iip_count += 1
            elif base.id == b'#IOP':
                self.sis.runtime.clear()
                self.sis.runtime.append(dg_data)
                self.sis5.iop_count += 1
            elif base.id == b'#SPO':
                self.sis5.spo_count += 1
            elif base.id == b'#MRZ':
                self.sis5.mrz_count += 1
            elif base.id == b'#SVP':
                self.sis.ssp.clear()
                self.sis.ssp.append(dg_data)
                self.sis5.svp_count += 1
            elif base.id == b'#SSM':
                self.sis5.ssm_count += 1

        self.sock_out.sendto(dg_data, (self.ip_out, self.port_out))

        with self._lock:
            time.sleep(self._replay_timing)

        return False

    def _sis_4(self, f, f_sz) -> bool:
        # guardian to avoid to read beyond the EOF
        if (f.tell() + 16) > f_sz:
            if self.debug:
                logger.debug("EOF")
            return True

        base = KngAll(verbose=True)
        ret = base.read(f, f_sz)
        if ret == KngAll.Flags.MISSING_FIRST_STX:

            if self.debug:
                logger.warning("troubles in reading file > SKIP")
            return True

        elif ret == KngAll.Flags.CORRUPTED_START_DATAGRAM:

            f.seek(-15, 1)  # +1 byte from initial header position
            logger.warning("troubles in reading initial datagram part > REALIGN to position: %s" % f.tell())
            return False

        elif ret == KngAll.Flags.UNEXPECTED_EOF:

            logger.warning("troubles in reading file > SKIP (reason: unexpected EOF)")
            return True

        elif ret == KngAll.Flags.CORRUPTED_END_DATAGRAM:

            f.seek(-(base.length + 3), 1)
            logger.warning("troubles in reading final datagram part > REALIGN to position: %s" % f.tell())

        elif ret == KngAll.Flags.VALID:

            self.dg_counter += 1

        else:
            raise RuntimeError("unknown return %s from KngAll" % ret)

        # Read and send only the desired datagrams:
        # - position (0x50)
        # - XYZ88 (0x58)
        # - sound speed profile (0x55)
        # - runtime parameters (0x52)
        # - installation parameters (0x49)
        # - range/angle (0x4e) for coverage modeling.
        # - seabed imagery (0x59)
        # - watercolumn (0x6b)
        if base.id in [0x4e, 0x49, 0x50, 0x52, 0x55, 0x58, 0x59, 0x6b]:
            logger.debug("%s %s > sending dg #%s(%s) (length: %sB)"
                         % (base.date, base.time, hex(base.id), base.id, base.length))
            f.seek(-base.length, 1)
            dg_data = f.read(base.length)

            # Stores a few datagrams of interest in data lists:
            with self.sis.lists_lock:
                if base.id == 0x49:
                    self.sis.installation.clear()
                    self.sis.installation.append(dg_data)
                    self.sis4.installation_count += 1
                elif base.id == 0x4e:
                    self.sis4.range_angle78_count += 1
                elif base.id == 0x50:
                    self.sis4.nav_count += 1
                elif base.id == 0x52:
                    self.sis.runtime.clear()
                    self.sis.runtime.append(dg_data)
                    self.sis4.runtime_count += 1
                elif base.id == 0x55:
                    self.sis.ssp.clear()
                    self.sis.ssp.append(dg_data)
                    self.sis4.ssp_count += 1
                elif base.id == 0x58:
                    self.sis4.xyz88_count += 1
                elif base.id == 0x6b:
                    self.sis4.watercolumn_count += 1

            self.sock_out.sendto(dg_data, (self.ip_out, self.port_out))

            with self._lock:
                time.sleep(self._replay_timing)

        return False

    def info(self) -> str:
        msg = "Transmitted datagrams:\n"

        if self.use_sis5:
            msg += "- IIP: %d\n" % self.sis5.iip_count
            msg += "- IOP: %d\n" % self.sis5.iop_count
            msg += "- MRZ: %d\n" % self.sis5.mrz_count
            msg += "- SPO: %d\n" % self.sis5.spo_count
            msg += "- SSM: %d\n" % self.sis5.ssm_count
            msg += "- SVP: %d\n" % self.sis5.svp_count
        else:
            msg += "- Raw: %d\n" % self.sis4.range_angle78_count
            msg += "- Nav: %d\n" % self.sis4.nav_count
            msg += "- Xyz: %d\n" % self.sis4.xyz88_count
            msg += "- Ssp: %d\n" % self.sis4.ssp_count
            msg += "- Runtime: %d\n" % self.sis4.runtime_count
            msg += "- Wcd: %d\n" % self.sis4.watercolumn_count

        return msg
