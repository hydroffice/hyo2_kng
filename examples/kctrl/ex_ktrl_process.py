import logging
import os
import time
from multiprocessing import Pipe, freeze_support
from hyo2.abc.lib.testing import Testing
from hyo2.kng.emu.kctrl.lib.kctrl_process import KCtrlProcess


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

data_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
testing = Testing(root_folder=data_folder)
test_files = testing.download_test_files(ext=".kmall")

if __name__ == '__main__':
    freeze_support()

    ip_out = "224.1.20.40"
    port_out = 6020

    logger.debug("starting SIS5 process ...")
    parent_conn, child_conn = Pipe()
    p = KCtrlProcess(conn=child_conn, ip_out=ip_out, port_out=port_out)
    p.set_files(test_files)
    p.start()

    count = 0
    while True:

        if not p.is_alive():
            break

        if count == 10:
            logger.debug("trigger termination")
            p.stop()

        count += 1
        logger.debug(" ... %d ..." % count)
        time.sleep(0.5)

    logger.debug("KCtrl process is alive? %s" % p.is_alive())
    logger.debug('%s.exitcode = %s' % (p.name, p.exitcode))  # <0: killed with signal; >0: exited with error
