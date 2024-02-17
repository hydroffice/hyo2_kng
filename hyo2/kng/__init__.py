import logging
import os

from hyo2.abc.lib.lib_info import LibInfo

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

name = "Kng"
__version__ = "1.3.0"
__author__ = "gmasetti@ccom.unh.edu"
__license__ = "LGPLv3 license"
__copyright__ = "Copyright 2024 University of New Hampshire, Center for Coastal and Ocean Mapping."

lib_info = LibInfo()

lib_info.lib_name = name
lib_info.lib_version = __version__
lib_info.lib_author = "Giuseppe Masetti(UNH,JHC-CCOM)"
lib_info.lib_author_email = "gmasetti@ccom.unh.edu"

lib_info.lib_license = "LGPLv3"
lib_info.lib_license_url = "https://www.hydroffice.org/license/"

lib_info.lib_path = os.path.abspath(os.path.dirname(__file__))

lib_info.lib_url = "https://www.hydroffice.org/sis_emu/"
lib_info.lib_manual_url = "https://www.hydroffice.org/manuals/kng/index.html"
lib_info.lib_support_email = "sis_emu@hydroffice.org"
lib_info.lib_latest_url = "https://www.hydroffice.org/latest/sis_emu.txt"

lib_info.lib_dep_dict = {
    "hyo2.abc": "hyo2.abc",
    "PySide2": "PySide2"
}
