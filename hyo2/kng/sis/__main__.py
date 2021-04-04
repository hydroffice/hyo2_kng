import sys
from multiprocessing import freeze_support
from PySide2 import QtWidgets

from hyo2.abc.lib.logging import set_logging
from hyo2.kng.sis.app import mainwin

set_logging(ns_list=["hyo2.kng", ])


def main():
    """create the main windows and the event loop"""
    freeze_support()

    app = QtWidgets.QApplication(sys.argv)

    mw = mainwin.MainWin()
    mw.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
