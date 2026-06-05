import logging
import re
from datetime import datetime, timezone
from enum import StrEnum

import requests

from common.models import AgeRating, ComicInfo
from src.__version__ import __version__
from src.Common.errors import MangaNotFoundError
from src.DynamicLibController.models.IMetadataSource import IMetadataSource
from src.Settings.SettingControl import SettingControl
from src.Settings.SettingControlType import SettingControlType
from src.Settings.SettingSection import SettingSection
from src.Settings.Settings import Settings


class NhentaiSetting(StrEnum):
    ApiKey = "api_key"
    UserAgent = "user_agent"
    TimeoutSeconds = "timeout_seconds"


class Nhentai(IMetadataSource):
    name = "Nhentai"
    _log = logging.getLogger()
    api_base_url = "https://nhentai.net/api/v2"
    gallery_url_template = "https://nhentai.net/g/{gallery_id}/"
    user_agent = f"MangaManager/{__version__.split(':')[0]} (https://github.com/Dormiveglia0/Manga-Manager)"
    api_key = ""
    timeout_seconds = 15
    last_error_title_key = None
    last_error_body_key = None

    _gallery_id_patterns = (
        re.compile(r"(?:https?://)?(?:www\.)?nhentai\.net/g/(\d+)", re.IGNORECASE),
        re.compile(r"(?:https?://)?(?:www\.)?nhentai\.net/api/v2/galleries/(\d+)", re.IGNORECASE),
    )

    def init_settings(self):
        self.settings = [
            SettingSection(self.name, self.name, [
                SettingControl(NhentaiSetting.ApiKey, "API Key", SettingControlType.Text, "",
                               "Optional. Sent as 'Authorization: Key <api_key>'."),
                SettingControl(NhentaiSetting.UserAgent, "User-Agent", SettingControlType.Text, self.user_agent,
                               "Descriptive User-Agent sent to nhentai API."),
                SettingControl(NhentaiSetting.TimeoutSeconds, "Timeout Seconds", SettingControlType.Text, "15",
                               "Request timeout in seconds."),
            ])
        ]
        super().init_settings()

    def save_settings(self):
        self.__class__.api_key = Settings().get(self.name, NhentaiSetting.ApiKey) or ""
        self.__class__.user_agent = Settings().get(self.name, NhentaiSetting.UserAgent) or self.user_agent
        try:
            self.__class__.timeout_seconds = max(1, int(Settings().get(self.name, NhentaiSetting.TimeoutSeconds)))
        except (TypeError, ValueError):
            self.__class__.timeout_seconds = 15

    @classmethod
    def _set_error(cls, title_key, body_key):
        cls.last_error_title_key = title_key
        cls.last_error_body_key = body_key

    @classmethod
    def clear_error(cls):
        cls.last_error_title_key = None
        cls.last_error_body_key = None

    @classmethod
    def extract_gallery_id(cls, *values) -> int | None:
        for value in values:
            if value is None:
                continue
            candidate = str(value).strip()
            if not candidate:
                continue
            if candidate.isdigit():
                return int(candidate)
            for pattern in cls._gallery_id_patterns:
                match = pattern.search(candidate)
                if match:
                    return int(match.group(1))
        return None

    @classmethod
    def _get_headers(cls) -> dict:
        headers = {"User-Agent": cls.user_agent}
        if cls.api_key:
            headers["Authorization"] = f"Key {cls.api_key}"
        return headers

    @staticmethod
    def _join_tag_names(data: dict, tag_type: str) -> str:
        return ", ".join(tag["name"].strip() for tag in data.get("tags", [])
                         if tag.get("type") == tag_type and tag.get("name"))

    @classmethod
    def _map_gallery_to_cinfo(cls, data: dict, gallery_id: int) -> ComicInfo:
        comicinfo = ComicInfo()
        title = data.get("title") or {}

        comicinfo.series = (title.get("pretty") or title.get("english") or "").strip()
        comicinfo.localized_series = (title.get("japanese") or "").strip()
        comicinfo.tags = cls._join_tag_names(data, "tag")
        comicinfo.genre = cls._join_tag_names(data, "category")
        comicinfo.characters = cls._join_tag_names(data, "character")
        comicinfo.series_group = cls._join_tag_names(data, "group")

        artists = cls._join_tag_names(data, "artist")
        comicinfo.writer = artists
        comicinfo.penciller = artists
        comicinfo.cover_artist = artists

        comicinfo.page_count = data.get("num_pages") or ""
        comicinfo.web = cls.gallery_url_template.format(gallery_id=gallery_id)
        comicinfo.age_rating = AgeRating.ADULTS_ONLY_18.value

        upload_date = data.get("upload_date")
        if upload_date:
            date = datetime.fromtimestamp(int(upload_date), tz=timezone.utc)
            comicinfo.year = date.year
            comicinfo.month = date.month
            comicinfo.day = date.day

        return comicinfo

    @classmethod
    def get_cinfo(cls, comic_info_from_ui: ComicInfo) -> ComicInfo | None:
        cls.clear_error()
        gallery_id = cls.extract_gallery_id(
            comic_info_from_ui.web,
            comic_info_from_ui.series,
            comic_info_from_ui.title,
        )
        if gallery_id is None:
            cls._log.warning("Nhentai gallery id could not be parsed from Web, Series or Title.")
            cls._set_error("message.nhentai_missing_id_title", "message.nhentai_missing_id_body")
            return None

        url = f"{cls.api_base_url}/galleries/{gallery_id}"
        try:
            response = requests.get(url, headers=cls._get_headers(), timeout=cls.timeout_seconds)
        except requests.RequestException:
            cls._log.exception("Unhandled exception making the request to nhentai.")
            cls._set_error("message.nhentai_network_title", "message.nhentai_network_body")
            return None

        if response.status_code == 404:
            raise MangaNotFoundError(cls.name, str(gallery_id))
        if response.status_code == 429:
            cls._log.warning("Nhentai API rate limit hit.")
            cls._set_error("message.nhentai_rate_limit_title", "message.nhentai_rate_limit_body")
            return None

        try:
            response.raise_for_status()
            data = response.json()
        except (requests.HTTPError, ValueError):
            cls._log.exception("Unexpected response from nhentai API.")
            cls._set_error("message.nhentai_network_title", "message.nhentai_network_body")
            return None

        return cls._map_gallery_to_cinfo(data, gallery_id)
