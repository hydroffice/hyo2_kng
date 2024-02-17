import logging
import os

from hyo2.abc2.lib.package.pkg_info import PkgInfo

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

name = "Kng"
__version__ = "1.3.0"
__author__ = "gmasetti@ccom.unh.edu"

pkg_info = PkgInfo(
    name=name,
    version=__version__,
    author="Giuseppe Masetti",
    author_email="gmasetti@ccom.unh.edu",
    lic="LGPLv3",
    lic_url="https://www.hydroffice.org/license/",
    path=os.path.abspath(os.path.dirname(__file__)),
    url="https://www.hydroffice.org/sis_emu/",
    manual_url="https://www.hydroffice.org/manuals/kng/index.html",
    support_email="sis_emu@hydroffice.org",
    latest_url="https://www.hydroffice.org/latest/sis_emu.txt",
    deps_dict={
        "hyo2.abc2": "hyo2.abc2",
        "PySide6": "PySide6"
    }
)
