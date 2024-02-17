import os
from hyo2.kng import pkg_info

app_path = os.path.abspath(os.path.dirname(__file__))
app_media_path = os.path.join(app_path, "media")
app_info = pkg_info.app_info(
    app_name="SISEmu",
    app_path=app_path,
    app_media_path=app_media_path,
    app_license_path=os.path.join(app_media_path, "LICENSE"),
    app_icon_path=os.path.join(app_media_path, "app_icon.png")
)
