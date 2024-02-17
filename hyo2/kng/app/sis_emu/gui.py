import logging
import sys
import traceback

from PySide6 import QtCore, QtWidgets

from hyo2.abc2.lib.logging import set_logging
from hyo2.abc2.app.app_style.app_style import AppStyle
from hyo2.kng.app.sis_emu.mainwin import MainWin

logger = logging.getLogger(__name__)
set_logging(ns_list=["hyo2.kng", ])


def qt_custom_handler(error_type: QtCore.QtMsgType, error_context: QtCore.QMessageLogContext, message: str):
    if "Cannot read property 'id' of null" in message:
        return
    if "GLImplementation: desktop" in message:
        return
    logger.info("Qt error: %s [%s] -> %s"
                % (error_type, error_context, message))

    for line in traceback.format_stack():
        logger.debug("- %s" % line.strip())


QtCore.qInstallMessageHandler(qt_custom_handler)


def gui():
    """create the main windows and the event loop"""
    app = QtWidgets.QApplication(sys.argv)
    AppStyle.apply(app=app)

    main = MainWin()
    main.show()

    sys.exit(app.exec())
