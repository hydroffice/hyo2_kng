import logging
import sys
from PySide2 import QtWidgets

from hyo2.abc.lib.logging import set_logging
from hyo2.kng.app.sis_emu.mainwin import MainWin

logger = logging.getLogger(__name__)
set_logging(ns_list=["hyo2.kng", ])


def gui():
    """create the main windows and the event loop"""
    app = QtWidgets.QApplication(sys.argv)

    main = MainWin()
    main.show()

    sys.exit(app.exec_())
