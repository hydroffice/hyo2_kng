import logging
import os
import time
from multiprocessing import freeze_support
from hyo2.abc2.lib.testing import Testing
from hyo2.abc2.lib.logging import set_logging
from hyo2.kng.lib.sis import Sis

set_logging(ns_list=['hyo2.kng'])
logger = logging.getLogger(__name__)

data_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
testing = Testing(root_folder=data_folder)
test_files = testing.download_test_files(ext=".kmall")

ip_out = "localhost"
port_out = 16103
replay_ssm = True
replay_mrz = False

if __name__ == '__main__':
    freeze_support()

    logger.debug("starting SIS process ...")
    sis = Sis(ip_out=ip_out, port_out=port_out, use_sis5=True, replay_ssm=replay_ssm, replay_mrz=replay_mrz)
    sis.verbose = True
    sis.set_files(test_files)
    sis.start()
    time.sleep(10)
    sis.stop()
    logger.debug("SIS' SVP thread is alive? %s" % sis.t_svp.is_alive())
    logger.debug("SIS' replay thread is alive? %s" % sis.t_replay.is_alive())
