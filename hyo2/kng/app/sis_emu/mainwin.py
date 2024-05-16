import logging

from PySide6 import QtCore, QtGui, QtWidgets
from urllib.request import urlopen

from hyo2.abc2.lib.package.pkg_helper import PkgHelper
from hyo2.abc2.app.browser.web_renderer import WebRenderer
from hyo2.kng import pkg_info
from hyo2.kng.app.sis_emu import app_info
from hyo2.kng.app.sis_emu.controlpanel import ControlPanel

logger = logging.getLogger(__name__)


class MainWin(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self._web = WebRenderer()
        self._check_web_page()
        self._check_latest_release()

        self.name = app_info.app_name
        self.version = app_info.app_version
        logger.debug('%s v.%s' % (self.name, self.version))

        self.setWindowTitle('%s v.%s' % (self.name, self.version))
        # noinspection PyArgumentList
        _app = QtCore.QCoreApplication.instance()
        _app.setApplicationName('%s' % self.name)
        _app.setOrganizationName("HydrOffice")
        _app.setOrganizationDomain("hydroffice.org")

        # set icons
        self.setWindowIcon(QtGui.QIcon(app_info.app_icon_path))

        # noinspection PyArgumentList
        self.setMinimumSize(400, 600)

        self.panel = ControlPanel()
        self.setCentralWidget(self.panel)

    def _check_web_page(self, token: str = ""):
        try:
            if len(token) > 0:
                url = "%s_%s" % (PkgHelper(pkg_info=pkg_info).web_url(), token)
            else:
                url = "%s" % PkgHelper(pkg_info=pkg_info).web_url()
            self._web.open(url=url)
            logger.debug('check %s' % url)

        except Exception as e:
            logger.warning(e)

    @classmethod
    def _check_latest_release(cls):
        try:
            response = urlopen(pkg_info.latest_url, timeout=1)
            latest_version = response.read().split()[0].decode()
            cur_maj, cur_min, cur_fix = app_info.app_version.split('.')
            lat_maj, lat_min, lat_fix = latest_version.split('.')

            if int(lat_maj) > int(cur_maj):
                logger.info("new release available: %s" % latest_version)

            elif (int(lat_maj) == int(cur_maj)) and (int(lat_min) > int(cur_min)):
                logger.info("new release available: %s" % latest_version)

            elif (int(lat_maj) == int(cur_maj)) and (int(lat_min) == int(cur_min)) and (int(lat_fix) > int(cur_fix)):
                logger.info("new bugfix available: %s" % latest_version)

        except Exception as e:
            logger.warning(e)

    def _do_you_really_want(self, title="Quit", text="quit") -> int:
        """helper function that show to the user a message windows asking to confirm an action"""
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setIconPixmap(QtGui.QPixmap(app_info.app_icon_path).scaled(QtCore.QSize(36, 36)))
        msg_box.setText('Do you really want to %s?' % text)
        # noinspection PyUnresolvedReferences
        msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        return msg_box.exec()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """ actions to be done before close the app """
        reply = self._do_you_really_want("Quit", "quit %s" % self.name)

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:

            event.accept()
            self.panel.stop_emulation()
            super().closeEvent(event)

        else:
            event.ignore()
