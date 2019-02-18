"""Script to download data files from the BitBucket repository"""

# noinspection PyProtectedMember
from pip._internal import main as pip
import sys
import os.path
import shutil
import zipfile

try:
    import wget
except ImportError as e:
    print("> missing wget, trying to install it: %s" % e)
    try:
        pip(['install', 'wget'])
        import wget
    except Exception as e:
        print("  - unable to install wget: %s" % e)
        sys.exit(1)

# list of archives to download
data_files = [
    "0010_20181215_042649_PressureDrop.kmall",
    "0024_20180628_122700_ShipName.kmall",
    "0013_20150801_143015_Langseth.all",
    "3009_20120618_171230_ShipName.all"
]

# create an empty `downloaded` folder
downloaded_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "download")
if os.path.exists(downloaded_folder):
    shutil.rmtree(downloaded_folder)
os.makedirs(downloaded_folder)

# actually downloading the file with wget
for fid in data_files:
    uri = 'https://bitbucket.org/hydroffice/hyo_kng/downloads/' + fid
    print("> downloading %s" % uri)
    if os.path.isfile(fid):
        print("  - already downloaded: skipping!")
    else:
        wget.download(uri, bar=wget.bar_thermometer, out=downloaded_folder)
        print("  - OK")

print("--- DONE")
