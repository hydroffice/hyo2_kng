import logging
import os
import time
from multiprocessing import Process, Event
from multiprocessing.connection import Connection
from typing import Callable, Optional
import threading
# from hyo2.kng.emu.sis4.lib.threads.svp_thread import SvpThread
# from hyo2.kng.emu.sis4.lib.threads.replay_thread import ReplayThread

logger = logging.getLogger(__name__)


class Top4Sis4Process(Process):
    """Topside for SIS4 process simulator"""

    def __init__(self, conn: Connection,
                 topside_port: int = 4001, sis4_port: int = 16103, sis4_ip: str = "localhost",
                 target: Optional[Callable] = None, name: Optional[str] = "SIS4",
                 verbose: bool = False):
        Process.__init__(self, target=target, name=name)
        self.conn = conn
        # self.daemon = True
        self.verbose = verbose

        # user settings
        self.sis4_port = sis4_port
        self.sis4_ip = sis4_ip
        self.topside_port = topside_port

        # # threads
        # self.t_svp = None
        # self.t_replay = None
        #
        # self.ssp = list()
        # self.installation = list()
        # self.runtime = list()
        #
        # self.files = list()

        self.shutdown = Event()

    # def set_files(self, files):
    #     """set the files to be used by the simulator"""
    #     # logger.debug("setting files")
    #
    #     # clean files
    #     self.files = list()
    #     for f in files:
    #
    #         if not os.path.exists(f):
    #             if self.verbose:
    #                 logger.debug("skip file: %s" % f)
    #             continue
    #
    #         self.files.append(f)
    #         logger.debug("file added: %s" % self.files[-1])
    #
    #     if len(self.files) == 0:
    #         raise RuntimeError("Not valid file paths passed")

    def stop(self):
        """Stop the process"""
        self.shutdown.set()

    # def init_thread(self):
    #
    #     lists_lock = threading.Lock()
    #
    #     self.t_svp = SvpThread(runtime=self.runtime,
    #                            installation=self.installation,
    #                            ssp=self.ssp,
    #                            lists_lock=lists_lock,
    #                            port_in=self.port_in,
    #                            port_out=self.port_out,
    #                            ip_out=self.ip_out,
    #                            verbose=self.verbose)
    #     self.t_svp.start()
    #
    #     self.t_replay = ReplayThread(runtime=self.runtime,
    #                                  installation=self.installation,
    #                                  ssp=self.ssp,
    #                                  lists_lock=lists_lock,
    #                                  files=self.files,
    #                                  replay_timing=self._replay_timing,
    #                                  port_in=self.port_in,
    #                                  port_out=self.port_out,
    #                                  ip_out=self.ip_out,
    #                                  verbose=self.verbose)
    #     self.t_replay.start()
    #
    # @staticmethod
    # def init_logger():
    #     global logger
    #     logger = logging.getLogger()
    #     logger.setLevel(logging.NOTSET)
    #     ch = logging.StreamHandler()
    #     ch.setLevel(logging.DEBUG)  # change to WARNING to reduce verbosity, DEBUG for high verbosity
    #     ch_formatter = logging.Formatter('<PRC> %(levelname)-9s %(name)s.%(funcName)s:%(lineno)d > %(message)s')
    #     ch.setFormatter(ch_formatter)
    #     logger.addHandler(ch)
    #     logger = logging.getLogger(__name__)

    def run(self):
        """Start the simulation"""
        self.conn.send("%s started" % self.name)

    #     self.init_thread()

        count = 0
        while True:

            if self.shutdown.is_set():
                self.conn.send("shutdown")
                # self.t_replay.stop()
                # self.t_svp.stop()
                # self.t_replay.join()
                # self.t_svp.join()

                break

            # if self.conn.poll():
            #
            #     data = self.conn.recv()
            #
            #     if isinstance(data, float):
            #         logger.debug("new timing: %s" % data)
            #         self.t_replay.lock_data()
            #         self.t_replay.replay_timing = data
            #         self.t_replay.unlock_data()

            if (count % 100) == 0:
                msg = "#%04d: running" % count
                # logger.debug(msg)
                self.conn.send(msg)

            time.sleep(1)
            count += 1

        self.conn.send("%s stopped\n" % self.name)
