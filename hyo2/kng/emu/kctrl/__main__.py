import logging
import sys
from multiprocessing import freeze_support
from PySide2 import QtWidgets
from hyo2.kng.emu.kctrl.app import mainwin


def main():
    """create the main windows and the event loop"""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)-9s %(name)s.%(funcName)s:%(lineno)d > %(message)s")
    logging.getLogger("hyo2").setLevel(logging.INFO)
    logging.getLogger("hyo2.kng").setLevel(logging.DEBUG)

    freeze_support()

    app = QtWidgets.QApplication(sys.argv)

    mw = mainwin.MainWin()
    mw.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
