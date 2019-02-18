import logging
import os
from multiprocessing import Pipe
from threading import Timer
from PySide2 import QtCore, QtGui, QtWidgets
from hyo2.kng.top.top4sis4.lib.top4sis4_process import Top4Sis4Process
from hyo2.kng.top.top4sis4.app.infoviewer import InfoViewerDialog
from hyo2.abc.app.qt_progress import QtProgress

logger = logging.getLogger(__name__)


class ControlPanel(QtWidgets.QWidget):
    here = os.path.abspath(os.path.dirname(__file__)).replace("\\", "/")

    def __init__(self):
        super(ControlPanel, self).__init__()
        self.topside = None

        # default settings
        self.default_sis4_port = "4001"
        self.default_sis4_ip = "127.0.0.1"
        self.default_topside_port = "16103"

        self.vbox = QtWidgets.QVBoxLayout()
        self.setLayout(self.vbox)

        self.settings = QtWidgets.QGroupBox("settings")
        self.settings.setStyleSheet("QGroupBox::title { color: rgb(155, 155, 155); }")
        self.vbox.addWidget(self.settings)
        self.set_topside_port = None
        self.set_sis4_ip = None
        self.set_sis4_port = None
        self._make_settings()

        self.commands = QtWidgets.QGroupBox("commands")
        self.commands.setStyleSheet("QGroupBox::title { color: rgb(155, 155, 155); }")
        self.vbox.addWidget(self.commands)
        self.start = None
        self.stop = None
        self._make_commands()

        self.messages = QtWidgets.QGroupBox("messages")
        self.messages.setStyleSheet("QGroupBox::title { color: rgb(155, 155, 155); }")
        self.vbox.addWidget(self.messages)
        self._make_messages()

        self.vbox.addSpacing(12)
        comments = QtWidgets.QLabel("<i>Comments and suggestions:</i> "
                                    "<a href='mailto:gmasetti@ccom.unh.edu'>gmasetti@ccom.unh.edu</a>")
        comments.setOpenExternalLinks(True)
        self.vbox.addWidget(comments)

        # info viewer
        self.info_viewer = InfoViewerDialog(self)

        # processing pipe
        self.conn = None
        self.child_conn = None
        self._active = False

    def _make_settings(self):
        """build 'settings' groupbox"""

        vbox = QtWidgets.QVBoxLayout()
        self.settings.setLayout(vbox)

        # topside port
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        text_input_port = QtWidgets.QLabel("Topside port:")
        hbox.addWidget(text_input_port)
        text_input_port.setMinimumWidth(80)
        self.set_topside_port = QtWidgets.QLineEdit("")
        hbox.addWidget(self.set_topside_port)
        validator = QtGui.QIntValidator(0, 65535)
        self.set_topside_port.setValidator(validator)

        # sis4 ip
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        text_sis4_ip = QtWidgets.QLabel("SIS4 IP:")
        hbox.addWidget(text_sis4_ip)
        text_sis4_ip.setMinimumWidth(80)
        self.set_sis4_ip = QtWidgets.QLineEdit("")
        hbox.addWidget(self.set_sis4_ip)
        octet = "(?:[0-1]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])"
        reg_ex = QtCore.QRegExp(r"^%s\.%s\.%s\.%s$" % (octet, octet, octet, octet))
        validator = QtGui.QRegExpValidator(reg_ex)
        self.set_sis4_ip.setValidator(validator)

        # sis4 port
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        text_sis4_port = QtWidgets.QLabel("SIS4 port:")
        hbox.addWidget(text_sis4_port)
        text_sis4_port.setMinimumWidth(80)
        self.set_sis4_port = QtWidgets.QLineEdit("")
        hbox.addWidget(self.set_sis4_port)
        validator = QtGui.QIntValidator(0, 65535)
        self.set_sis4_port.setValidator(validator)

        vbox.addSpacing(4)

        # default values
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addStretch()
        button_defaults = QtWidgets.QPushButton()
        hbox.addWidget(button_defaults)
        button_defaults.setText("Use defaults")
        button_defaults.setToolTip('Set default values')
        # noinspection PyUnresolvedReferences
        button_defaults.clicked.connect(self.set_defaults)
        hbox.addStretch()

        vbox.addSpacing(12)

        # verbose
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        text_verbose = QtWidgets.QLabel("Verbose:")
        hbox.addWidget(text_verbose)
        text_verbose.setMinimumWidth(80)
        self.set_verbose = QtWidgets.QCheckBox()
        self.set_verbose.setChecked(True)
        hbox.addWidget(self.set_verbose)
        hbox.addStretch()

        self.set_defaults()

    def _make_commands(self):
        """build 'commands' groupbox"""

        vbox = QtWidgets.QVBoxLayout()
        self.commands.setLayout(vbox)

        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addStretch()

        button_start = QtWidgets.QPushButton()
        hbox.addWidget(button_start)
        button_start.setText("Start")
        button_start.setToolTip('Start listening using defined settings')
        # noinspection PyUnresolvedReferences
        button_start.clicked.connect(self.start_listening)

        button_stop_sis = QtWidgets.QPushButton()
        hbox.addWidget(button_stop_sis)
        button_stop_sis.setText("Stop")
        button_stop_sis.setToolTip('Stop listening')
        # noinspection PyUnresolvedReferences
        button_stop_sis.clicked.connect(self.stop_listening)

        hbox.addStretch()

    def _make_messages(self):
        """build 'messages' groupbox"""

        vbox = QtWidgets.QVBoxLayout()
        self.messages.setLayout(vbox)

        self.message_list = QtWidgets.QComboBox()
        vbox.addWidget(self.message_list)

        self.message_text = QtWidgets.QTextEdit()
        vbox.addWidget(self.message_text)

        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addStretch()

        button_send = QtWidgets.QPushButton()
        hbox.addWidget(button_send)
        button_send.setText("Send")
        button_send.setToolTip('Send message')
        # noinspection PyUnresolvedReferences
        button_send.clicked.connect(self.send_message)

        hbox.addStretch()

    # #################################################################################
    # ################################ action slots ###################################

    def set_defaults(self):
        self.set_topside_port.setText(self.default_topside_port)
        self.set_sis4_ip.setText(self.default_sis4_ip)
        self.set_sis4_port.setText(self.default_sis4_port)

    def listening(self):

        if self.conn is None:
            return

        if self.conn.poll():

            data = self.conn.recv()

            if isinstance(data, str):
                self.info_viewer.append(data)
                # logger.debug("%s" % data)

        if not self._active:
            return

        Timer(0.5, self.listening).start()

    def start_listening(self):
        if self.topside:
            if self.topside.is_alive():
                # noinspection PyCallByClass
                QtWidgets.QMessageBox.warning(self, "Listener running ...", "The listener is running! Stop it",
                                              QtWidgets.QMessageBox.Ok)
                return

        self.info_viewer.viewer.verticalScrollBar().setValue(self.info_viewer.viewer.verticalScrollBar().maximum())
        self.info_viewer.show()

        # create a new process
        topside_port = int(self.set_topside_port.text())
        sis4_ip = self.set_sis4_ip.text()
        sis4_port = int(self.set_sis4_port.text())
        self.conn, self.child_conn = Pipe()
        self.topside = Top4Sis4Process(conn=self.child_conn,
                                       topside_port=topside_port, sis4_port=sis4_port, sis4_ip=sis4_ip,
                                       verbose=self.set_verbose.isChecked())
        logger.debug('created new listener')

        self.topside.start()
        self._active = True
        self.listening()

    def stop_listening(self):
        logger.debug("stop Topside")
        if self.topside:
            progress = QtProgress(self)
            progress.start(title="Halting", text="Wait while threads stop")
            progress.update(value=20)
            self.topside.stop()

            progress.update(value=30)
            self.topside.join()
            self.topside = None

            progress.end()

        self._active = False
        self.info_viewer.hide()

    def send_message(self):
        logger.debug("send message")
