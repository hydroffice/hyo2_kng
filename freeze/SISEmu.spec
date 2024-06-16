# Builds a single-folder EXE for distribution.
# Note that an "unbundled" distribution launches much more quickly, but
# requires an installer program to distribute.
#
# To compile, execute the following within the source directory:
#
# python /path/to/pyinstaller.py sis_emu.spec
#
# The resulting .exe file is placed in the dist/SIS folder.
#
#
# Uploading to BitBucket: curl -s -v -u giumas:password -X POST https://api.bitbucket.org/2.0/repositories/hydroffice/hyo_kng/downloads -F files=@SISEmu.1.3.0.zip

from datetime import datetime
import os
import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, TOC
from PyInstaller.compat import is_darwin, is_win

from hyo2.kng import __version__ as sis_version

sys.setrecursionlimit(20000)

is_beta = False
if is_beta:
    beta = ".b%s" % datetime.now().strftime("%Y%m%d%H%M%S")
else:
    beta = str()


def collect_pkg_data(package, include_py_files=False, subdir=None):
    from PyInstaller.utils.hooks import get_package_paths, remove_prefix, PY_IGNORE_EXTENSIONS

    # Accept only strings as packages.
    if type(package) is not str:
        raise ValueError

    pkg_base, pkg_dir = get_package_paths(package)
    if subdir:
        pkg_dir = os.path.join(pkg_dir, subdir)
    # Walk through all file in the given package, looking for data files.
    data_toc = TOC()
    for dir_path, dir_names, files in os.walk(pkg_dir):
        for f in files:
            extension = os.path.splitext(f)[1]
            if include_py_files or (extension not in PY_IGNORE_EXTENSIONS):
                source_file = os.path.join(dir_path, f)
                dest_folder = remove_prefix(dir_path, os.path.dirname(pkg_base) + os.sep)
                dest_file = os.path.join(dest_folder, f)
                data_toc.append((dest_file, source_file, 'DATA'))

    return data_toc


def python_path() -> str:
    """ Return the python site-specific directory prefix (PyInstaller-aware) """

    # required by PyInstaller
    if hasattr(sys, '_MEIPASS'):

        if is_win():
            import win32api
            # noinspection PyProtectedMember
            sys_prefix = win32api.GetLongPathName(sys._MEIPASS)
        else:
            # noinspection PyProtectedMember
            sys_prefix = sys._MEIPASS

        print("using _MEIPASS: %s" % sys_prefix)
        return sys_prefix

    # check if in a virtual environment
    if hasattr(sys, 'real_prefix'):
        return sys.real_prefix

    return sys.prefix


def collect_folder_data(input_data_folder: str, relative_output_folder: str):

    data_toc = TOC()
    if not os.path.exists(input_data_folder):
        print("issue with folder: %s" % input_data_folder)
        return data_toc

    for dir_path, dir_names, files in os.walk(input_data_folder):
        for f in files:
            source_file = os.path.join(dir_path, f)
            dest_file = os.path.join(relative_output_folder, f)
            data_toc.append((dest_file, source_file, 'DATA'))
        break

    return data_toc


share_folder = os.path.join(python_path(), "Library", "share")
output_folder = os.path.join("Library", "share")
pyproj_data = collect_folder_data(input_data_folder=share_folder, relative_output_folder=output_folder)

abc2_data = collect_pkg_data('hyo2.abc2')
kng_data = collect_pkg_data('hyo2.kng')

icon_file = os.path.normpath(os.path.join(os.getcwd(), 'freeze', 'SISEmu.ico'))
if is_darwin:
    icon_file = os.path.normpath(os.path.join(os.getcwd(), 'freeze', 'SISEmu.icns'))

a = Analysis(['SISEmu.py'],
             pathex=[],
             hiddenimports=["PIL", "typing", "cftime._cftime", "pkg_resources"],
             excludes=["IPython", "PyQt4", "PyQt5", "PySide2", "pandas", "sphinx", "sphinx_rtd_theme",
                       "OpenGL_accelerate", "FixTk", "tcl", "tk", "_tkinter", "tkinter", "Tkinter",
                       "wx", "qgis"],
             hookspath=None,
             runtime_hooks=None)

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='SISEmu',
          debug=False,
          strip=None,
          upx=True,
          console=True,
          icon=icon_file)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               pyproj_data,
               abc2_data,
               kng_data,
               strip=None,
               upx=True,
               name='SISEmu.%s%s' % (sis_version, beta))
