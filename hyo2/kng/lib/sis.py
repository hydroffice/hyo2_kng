import logging
import os
import threading
from typing import List, Optional

from hyo2.kng.lib.threads.replay_thread import ReplayThread
from hyo2.kng.lib.threads.svp_thread import SvpThread

logger = logging.getLogger(__name__)


class Sis:
    """SIS simulator"""

    def __init__(self, port_in: int = 4001, port_out: int = 26103, ip_out: str = "localhost",
                 replay_timing: float = 1.0, use_sis5: bool = True, replay_ssm: bool = True, replay_mrz: bool = True,
                 verbose: bool = False):

        # user settings
        self.port_in = port_in
        self.port_out = port_out
        self.ip_out = ip_out
        self.use_sis5 = use_sis5
        self._replay_ssm = replay_ssm
        self._replay_mrz = replay_mrz
        self._replay_timing = replay_timing
        self.verbose = verbose

        # threads
        self.t_svp: Optional[SvpThread] = None
        self.t_replay: Optional[ReplayThread] = None

        self.ssp = list()  # type: List[bytes]
        self.installation = list()  # type: List[bytes]
        self.runtime = list()  # type: List[bytes]

        self.files = list()  # type: List[str]

    def set_files(self, files: List[str]) -> None:
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

    def stop(self) -> None:
        """Stop the process"""
        self.t_svp.stop()
        self.t_svp.join()

        self.t_replay.stop()
        self.t_replay.join()

    def start(self) -> None:

        lists_lock = threading.Lock()

        self.t_svp = SvpThread(
            runtime=self.runtime,
            installation=self.installation,
            ssp=self.ssp,
            lists_lock=lists_lock,
            port_in=self.port_in,
            port_out=self.port_out,
            ip_out=self.ip_out,
            debug=self.verbose,
            use_sis5=self.use_sis5)
        self.t_svp.start()

        self.t_replay = ReplayThread(
            runtime=self.runtime,
            installation=self.installation,
            ssp=self.ssp,
            lists_lock=lists_lock,
            files=self.files,
            replay_timing=self._replay_timing,
            port_out=self.port_out,
            ip_out=self.ip_out,
            use_sis5=self.use_sis5,
            debug=self.verbose,
            replay_ssm=self._replay_ssm,
            replay_mrz=self._replay_mrz
        )
        self.t_replay.start()

    def set_timing(self, timing: float) -> None:
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
