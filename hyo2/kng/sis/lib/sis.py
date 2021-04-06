import logging
import os
import threading
from hyo2.kng.sis.lib.threads.svp_thread import SvpThread
from hyo2.kng.sis.lib.threads.replay_thread import ReplayThread

logger = logging.getLogger(__name__)


class Sis:
    """SIS simulator"""

    def __init__(self, replay_timing=1.0, port_in=4001, port_out=26103, ip_out="localhost",
                 use_sis5: bool = False, debug=False):
        self.verbose = debug
        self._replay_timing = replay_timing

        # user settings
        self.port_in = port_in
        self.port_out = port_out
        self.ip_out = ip_out
        self.use_sis5 = use_sis5

        # threads
        self.t_svp = None
        self.t_replay = None

        self.ssp = list()
        self.installation = list()
        self.runtime = list()

        self.files = list()

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
        self.t_svp.stop()
        self.t_svp.join()

        self.t_replay.stop()
        self.t_replay.join()

    def start(self):

        lists_lock = threading.Lock()

        self.t_svp = SvpThread(runtime=self.runtime,
                               installation=self.installation,
                               ssp=self.ssp,
                               lists_lock=lists_lock,
                               port_in=self.port_in,
                               port_out=self.port_out,
                               ip_out=self.ip_out,
                               debug=self.verbose,
                               use_sis5=self.use_sis5)
        self.t_svp.start()

        self.t_replay = ReplayThread(runtime=self.runtime,
                                     installation=self.installation,
                                     ssp=self.ssp,
                                     lists_lock=lists_lock,
                                     files=self.files,
                                     replay_timing=self._replay_timing,
                                     port_out=self.port_out,
                                     ip_out=self.ip_out,
                                     use_sis5=self.use_sis5,
                                     debug=self.verbose)
        self.t_replay.start()

    def set_timing(self, timing: float):
        logger.debug('new timing: %s' % timing)
        self.t_replay.lock_data()
        self.t_replay.replay_timing = timing
        self.t_replay.unlock_data()

    def send_fake_profile(self) -> None:
        if self.t_svp:
            self.t_svp.send_fake_profile()

    def send_latest_profile(self) -> None:
        if self.t_svp:
            self.t_svp.send_latest_received_profile()

    def info(self) -> str:
        msg = str()
        if self.t_replay:
            msg += self.t_replay.info()
        msg += "\n"
        if self.t_svp:
            msg += self.t_svp.info()
        return msg
