import logging
import os
from PySide2 import QtCore, QtGui, QtWidgets
from hyo2.kng.sis.lib.sis import Sis
from hyo2.abc.app.qt_progress import QtProgress

logger = logging.getLogger(__name__)


class ControlPanel(QtWidgets.QWidget):
    here = os.path.abspath(os.path.dirname(__file__)).replace("\\", "/")

    def __init__(self):
        super(ControlPanel, self).__init__()
        self.sis = None

        # default SIS values
        self.default_sis4_input_port = "4001"
        self.default_sis5_input_port = "14002"
        self.default_sis_output_ip = "127.0.0.1"
        self.default_sis_output_port = "16103"

        self.vbox = QtWidgets.QVBoxLayout()
        self.setLayout(self.vbox)

        self.sis_settings = QtWidgets.QGroupBox("settings")
        self.sis_settings.setStyleSheet("QGroupBox::title { color: rgb(155, 155, 155); }")
        self.vbox.addWidget(self.sis_settings)
        self.sis_4 = None
        self.sis_5 = None
        self.set_input_port = None
        self.set_output_ip = None
        self.set_output_port = None
        self._make_sis_settings()

        self.sis_inputs = QtWidgets.QGroupBox("inputs")
        self.sis_inputs.setStyleSheet("QGroupBox::title { color: rgb(155, 155, 155); }")
        self.sis_inputs.setMaximumHeight(140)
        self.vbox.addWidget(self.sis_inputs)
        self.list_files = None
        self._make_sis_inputs()

        self.sis_commands = QtWidgets.QGroupBox("commands")
        self.sis_commands.setStyleSheet("QGroupBox::title { color: rgb(155, 155, 155); }")
        self.vbox.addWidget(self.sis_commands)
        self._make_sis_commands()

        # info viewer
        self.viewer = QtWidgets.QTextBrowser()
        self.viewer.resize(QtCore.QSize(320, 40))
        self.viewer.setTextColor(QtGui.QColor("#4682b4"))
        self.viewer.ensureCursorVisible()
        # create a monospace font
        font = QtGui.QFont("Courier New")
        font.setStyleHint(QtGui.QFont.TypeWriter)
        font.setFixedPitch(True)
        font.setPointSize(9)
        self.viewer.document().setDefaultFont(font)
        # set the tab size
        metrics = QtGui.QFontMetrics(font)
        # noinspection PyArgumentList
        self.viewer.setTabStopWidth(3 * metrics.width(' '))
        self.viewer.setReadOnly(True)
        self.vbox.addWidget(self.viewer)

        self.vbox.addSpacing(6)
        comments = QtWidgets.QLabel("<i>Comments and suggestions:</i> "
                                    "<a href='mailto:gmasetti@ccom.unh.edu'>gmasetti@ccom.unh.edu</a>")
        comments.setOpenExternalLinks(True)
        self.vbox.addWidget(comments)

        self.set_sis_4()  # to also clear the file list
        self.enable_commands(True)

        timer = QtCore.QTimer(self)
        # noinspection PyUnresolvedReferences
        timer.timeout.connect(self.update_gui)
        # noinspection PyArgumentList
        timer.start(1500)

        self._active = False
        self._replay_timing = 1.0

    def _make_sis_settings(self):
        """build "settings" groupbox"""

        vbox = QtWidgets.QVBoxLayout()
        self.sis_settings.setLayout(vbox)

        # default values
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        text_input_port = QtWidgets.QLabel("SIS Version:")
        hbox.addWidget(text_input_port)
        text_input_port.setMinimumWidth(80)
        self.sis_4 = QtWidgets.QRadioButton()
        hbox.addWidget(self.sis_4)
        self.sis_4.setText("SIS4")
        self.sis_4.setToolTip('Settings for SIS 4')
        self.sis_4.setChecked(True)
        # noinspection PyUnresolvedReferences
        self.sis_4.clicked.connect(self.set_sis_4)
        self.sis_5 = QtWidgets.QRadioButton()
        hbox.addWidget(self.sis_5)
        self.sis_5.setText("SIS5")
        self.sis_5.setToolTip('Settings for SIS 5')
        # noinspection PyUnresolvedReferences
        self.sis_5.clicked.connect(self.set_sis_5)
        hbox.addStretch()

        vbox.addSpacing(4)

        # input port
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        text_input_port = QtWidgets.QLabel("Input port:")
        hbox.addWidget(text_input_port)
        text_input_port.setMinimumWidth(80)
        self.set_input_port = QtWidgets.QLineEdit("")
        hbox.addWidget(self.set_input_port)
        validator = QtGui.QIntValidator(0, 65535)
        self.set_input_port.setValidator(validator)

        # output ip
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        text_output_ip = QtWidgets.QLabel("Output IP:")
        hbox.addWidget(text_output_ip)
        text_output_ip.setMinimumWidth(80)
        self.set_output_ip = QtWidgets.QLineEdit("")
        hbox.addWidget(self.set_output_ip)
        octet = "(?:[0-1]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])"
        reg_ex = QtCore.QRegExp(r"^%s\.%s\.%s\.%s$" % (octet, octet, octet, octet))
        validator = QtGui.QRegExpValidator(reg_ex)
        self.set_output_ip.setValidator(validator)

        # output port
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        text_output_port = QtWidgets.QLabel("Output port:")
        hbox.addWidget(text_output_port)
        text_output_port.setMinimumWidth(80)
        self.set_output_port = QtWidgets.QLineEdit("")
        hbox.addWidget(self.set_output_port)
        validator = QtGui.QIntValidator(0, 65535)
        self.set_output_port.setValidator(validator)

        vbox.addSpacing(12)

        # replay timing
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        text_timing = QtWidgets.QLabel("Timing:")
        hbox.addWidget(text_timing)
        text_timing.setMinimumWidth(80)
        self.set_timing = QtWidgets.QSlider()
        # noinspection PyUnresolvedReferences
        self.set_timing.setOrientation(QtCore.Qt.Horizontal)
        self.set_timing.setMinimum(1)
        self.set_timing.setMaximum(5)
        self.set_timing.setTickInterval(1)
        self.set_timing.setValue(1)
        self.set_timing.setTickPosition(QtWidgets.QSlider.TicksBelow)
        # noinspection PyUnresolvedReferences
        self.set_timing.valueChanged.connect(self.on_replay_timing)
        hbox.addWidget(self.set_timing)

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

    def set_sis_4(self):
        self.list_files.clear()
        self.set_input_port.setText(self.default_sis4_input_port)
        self.set_output_ip.setText(self.default_sis_output_ip)
        self.set_output_port.setText(self.default_sis_output_port)

    def set_sis_5(self):
        self.list_files.clear()
        self.set_input_port.setText(self.default_sis5_input_port)
        self.set_output_ip.setText(self.default_sis_output_ip)
        self.set_output_port.setText(self.default_sis_output_port)

    def enable_commands(self, enable: bool):
        self.sis_4.setEnabled(enable)
        self.sis_5.setEnabled(enable)
        self.set_input_port.setEnabled(enable)
        self.set_output_ip.setEnabled(enable)
        self.set_output_port.setEnabled(enable)
        self.set_verbose.setEnabled(enable)
        self.button_add_files.setEnabled(enable)
        self.button_clear_files.setEnabled(enable)
        self.button_start_sis.setEnabled(enable)
        self.button_send_fake.setDisabled(enable)
        self.button_send_latest.setDisabled(enable)
        self.button_stop_sis.setDisabled(enable)

    def _make_sis_inputs(self):

        vbox = QtWidgets.QVBoxLayout()
        self.sis_inputs.setLayout(vbox)

        self.list_files = QtWidgets.QListWidget()
        self.list_files.setFixedHeight(60)
        vbox.addWidget(self.list_files)

        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addStretch()

        self.button_add_files = QtWidgets.QPushButton()
        hbox.addWidget(self.button_add_files)
        self.button_add_files.setText("Add files")
        self.button_add_files.setToolTip('Add files as data source for emulation')
        # noinspection PyUnresolvedReferences
        self.button_add_files.clicked.connect(self._add_source_files)

        self.button_clear_files = QtWidgets.QPushButton()
        hbox.addWidget(self.button_clear_files)
        self.button_clear_files.setText("Clear files")
        self.button_clear_files.setToolTip('Clear the file list')
        # noinspection PyUnresolvedReferences
        self.button_clear_files.clicked.connect(self._clear_source_files)

        hbox.addStretch()

    def _make_sis_commands(self):
        """build "commands" groupbox"""

        vbox = QtWidgets.QVBoxLayout()
        self.sis_commands.setLayout(vbox)

        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addStretch()

        self.button_start_sis = QtWidgets.QPushButton()
        hbox.addWidget(self.button_start_sis)
        self.button_start_sis.setText("Start SIS")
        self.button_start_sis.setToolTip('Start emulation using defined settings')
        # noinspection PyUnresolvedReferences
        self.button_start_sis.clicked.connect(self.start_emulation)
        
        self.button_send_fake = QtWidgets.QPushButton()
        hbox.addWidget(self.button_send_fake)
        self.button_send_fake.setText("Send fake SSP")
        self.button_send_fake.setToolTip('Send a fake sound speed profile')
        # noinspection PyUnresolvedReferences
        self.button_send_fake.clicked.connect(self.send_fake)
        
        self.button_send_latest = QtWidgets.QPushButton()
        hbox.addWidget(self.button_send_latest)
        self.button_send_latest.setText("Send latest SSP")
        self.button_send_latest.setToolTip('Send the latest received sound speed profile')
        # noinspection PyUnresolvedReferences
        self.button_send_latest.clicked.connect(self.send_latest)

        self.button_stop_sis = QtWidgets.QPushButton()
        hbox.addWidget(self.button_stop_sis)
        self.button_stop_sis.setText("Stop SIS")
        self.button_stop_sis.setToolTip('Stop emulation')
        # noinspection PyUnresolvedReferences
        self.button_stop_sis.clicked.connect(self.stop_emulation)

        hbox.addStretch()

    # #################################################################################
    # ################################ action slots ###################################

    def _add_source_files(self):
        logger.debug('adding files')

        settings = QtCore.QSettings()
        source_folder = settings.value("source_folder", self.here)

        # ask the file path to the user
        if self.sis_4.isChecked():
            # noinspection PyCallByClass
            selections, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Add Kongsberg data files", source_folder,
                                                                   "EM .all files (*.all *.wcd);;"
                                                                   "All files (*.*)", "")
        elif self.sis_5.isChecked():
            # noinspection PyCallByClass
            selections, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Add Kongsberg data files", source_folder,
                                                                   "KMall .kmall files (*.kmall);;"
                                                                   "All files (*.*)", "")
        else:
            raise RuntimeError('Invalid SIS type')

        if not selections:
            logger.debug('no selection')
            return

        selected_folder = os.path.dirname(selections[0])
        logger.debug("selected folder: %s" % selected_folder)
        settings.setValue("source_folder", selected_folder)

        for f in selections:
            # noinspection PyUnresolvedReferences
            ret = self.list_files.findItems(f, QtCore.Qt.MatchExactly)
            if len(ret) > 0:
                logger.debug('duplicated %s' % os.path.basename(f))
                # noinspection PyCallByClass,PyArgumentList
                QtWidgets.QMessageBox.warning(self, "File Duplication",
                                              "Attempt to add a listed file:\n%s" % os.path.basename(f),
                                              QtWidgets.QMessageBox.Ok)
                continue
            item = QtWidgets.QListWidgetItem(f)
            self.list_files.addItem(item)
            logger.debug('added %s' % os.path.basename(f))

    def _clear_source_files(self):
        logger.debug('clear source files')
        self.list_files.clear()

    def start_emulation(self):
        self.viewer.clear()
        self.enable_commands(enable=False)

        # create a new process
        input_port = int(self.set_input_port.text())
        output_ip = self.set_output_ip.text()
        output_port = int(self.set_output_port.text())
        self.sis = Sis(port_in=input_port, port_out=output_port, ip_out=output_ip,
                       replay_timing=self._replay_timing, use_sis5=self.sis_5.isChecked(),
                       debug=self.set_verbose.isChecked())
        logger.debug('created new simulator')

        file_list = list()
        for i in range(self.list_files.count()):

            logger.debug("passing file: %s" % self.list_files.item(i).text())
            file_path = self.list_files.item(i).text()
            if os.path.exists(file_path):
                file_list.append(file_path)

        if len(file_list) > 0:
            logger.debug('added source files: %s' % len(file_list))

            self.sis.set_files(file_list)

        self.sis.start()

    def stop_emulation(self):
        logger.debug("stop SIS")
        if self.sis:
            progress = QtProgress(self)
            progress.start(title="Halting", text="Wait while threads stop")
            progress.update(value=20)
            self.sis.stop()

            progress.update(value=30)
            self.sis = None

            progress.end()

        self.enable_commands(enable=True)

    def send_fake(self):
        if self.sis:
            self.sis.send_fake_profile()

    def send_latest(self):
        if self.sis:
            self.sis.send_latest_profile()

    def on_replay_timing(self):
        value = self.set_timing.value()

        if value == 1:
            self._replay_timing = 1.0

        elif value == 2:
            self._replay_timing = 0.5

        elif value == 3:
            self._replay_timing = 0.1

        elif value == 4:
            self._replay_timing = 0.01

        else:
            self._replay_timing = 0.0001

        if self.sis is not None:
            self.sis.set_timing(self._replay_timing)

        logger.debug("changed timing: %.4f" % self._replay_timing)

    def update_gui(self):
        if self.sis is None:
            self.viewer.clear()
            return
        self.viewer.setText(self.sis.info())
