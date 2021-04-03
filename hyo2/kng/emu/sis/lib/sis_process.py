import logging
import os
import time
from multiprocessing import Process, Event
import threading
from hyo2.kng.emu.sis.lib.threads.svp_thread import SvpThread
from hyo2.kng.emu.sis.lib.threads.replay_thread import ReplayThread

logger = logging.getLogger(__name__)


class SisProcess(Process):
    """SIS process simulator"""

    def __init__(self, conn, replay_timing=1.0, port_in=4001, port_out=26103, ip_out="localhost",
                 target=None, name="SIS", sis5: bool=False, verbose=False):
        Process.__init__(self, target=target, name=name)
        self.conn = conn
        self.daemon = True
        self.verbose = verbose
        self._replay_timing = replay_timing

        # user settings
        self.port_in = port_in
        self.port_out = port_out
        self.ip_out = ip_out
        self.sis5 = sis5

        # threads
        self.t_svp = None
        self.t_replay = None

        self.ssp = list()
        self.installation = list()
        self.runtime = list()

        self.files = list()

        self.shutdown = Event()

    def set_files(self, files):
        """set the files to be used by the simulator"""
        # logger.debug("setting files")

        # clean files
        self.files = list()
        for f in files:

            if not os.path.exists(f):
                if self.verbose:
                    logger.debug("skip file: %s" % f)
                continue

            self.files.append(f)
            logger.debug("file added: %s" % self.files[-1])

        if len(self.files) == 0:
            raise RuntimeError("Not valid file paths passed")

    def stop(self):
        """Stop the process"""
        self.shutdown.set()

    def init_thread(self):

        lists_lock = threading.Lock()

        if self.sis5:

            logger.debug('SVP uncoded for SIS5')

        else:  # SIS 4

            self.t_svp = SvpThread(runtime=self.runtime,
                                   installation=self.installation,
                                   ssp=self.ssp,
                                   lists_lock=lists_lock,
                                   port_in=self.port_in,
                                   port_out=self.port_out,
                                   ip_out=self.ip_out,
                                   verbose=self.verbose)
            self.t_svp.start()

        self.t_replay = ReplayThread(runtime=self.runtime,
                                     installation=self.installation,
                                     ssp=self.ssp,
                                     lists_lock=lists_lock,
                                     files=self.files,
                                     replay_timing=self._replay_timing,
                                     port_out=self.port_out,
                                     ip_out=self.ip_out,
                                     sis5=self.sis5,
                                     verbose=self.verbose)
        self.t_replay.start()

    def run(self):
        """Start the simulation"""
        # self.init_logger()
        self.conn.send("%s started" % self.name)

        self.init_thread()

        count = 0
        while True:

            if self.shutdown.is_set():
                self.conn.send("shutdown")

                if self.sis5:
                    logger.debug('SVP uncoded for SIS5')

                else:
                    self.t_svp.stop()
                    self.t_svp.join()

                self.t_replay.stop()
                self.t_replay.join()
                break

            if self.conn.poll():

                data = self.conn.recv()

                if isinstance(data, float):
                    logger.debug("new timing: %s" % data)

                    self.t_replay.lock_data()
                    self.t_replay.replay_timing = data
                    self.t_replay.unlock_data()

            if (count % 100) == 0:
                msg = "#%04d: running" % count
                # logger.debug(msg)
                self.conn.send(msg)

            time.sleep(1)
            count += 1

        self.conn.send("%s stopped\n" % self.name)
