import logging

from common.models import ComicInfo
from src.DynamicLibController.models.IMetadataSource import IMetadataSource
from src.Settings.SettingControl import SettingControl
from src.Settings.SettingControlType import SettingControlType
from src.Settings.SettingSection import SettingSection


class Nhentai(IMetadataSource):
    name = "Nhentai"
    _log = logging.getLogger()
    is_placeholder = True

    def init_settings(self):
        self.settings = [
            SettingSection(self.name, self.name, [
                SettingControl("enabled_placeholder", "Reserved provider", SettingControlType.Bool, False,
                               "Nhentai scraping is reserved but not implemented yet."),
            ])
        ]
        super().init_settings()

    @classmethod
    def get_cinfo(cls, comic_info_from_ui: ComicInfo) -> ComicInfo | None:
        cls._log.warning("Nhentai metadata source is reserved but not implemented yet.")
        return None
