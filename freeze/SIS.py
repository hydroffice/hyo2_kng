import logging
import sys
from multiprocessing import freeze_support

from PySide2 import QtWidgets

from hyo2.abc.lib.logging import set_logging
from hyo2.kng.emu.sis.app.mainwin import MainWin

logger = logging.getLogger(__name__)
set_logging(ns_list=["hyo2.kng", ])


def sis_gui():
    """create the main windows and the event loop"""
    app = QtWidgets.QApplication(sys.argv)

    main = MainWin()
    main.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    freeze_support()
    sis_gui()
