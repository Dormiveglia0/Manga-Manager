import unittest
from unittest.mock import Mock, patch

import requests

from ExternalSources.MetadataSources.Providers.Nhentai import Nhentai
from common.models import AgeRating, ComicInfo
from src.Common.errors import MangaNotFoundError


def _response(status_code=200, data=None):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = data or {}
    response.raise_for_status.side_effect = requests.HTTPError() if status_code >= 400 else None
    return response


class NhentaiTests(unittest.TestCase):
    def setUp(self):
        Nhentai.clear_error()
        Nhentai.api_key = ""
        Nhentai.user_agent = "MangaManager/test"
        Nhentai.timeout_seconds = 15

    def test_extract_gallery_id_from_supported_inputs(self):
        self.assertEqual(12345, Nhentai.extract_gallery_id("https://nhentai.net/g/12345/"))
        self.assertEqual(23456, Nhentai.extract_gallery_id("https://nhentai.net/api/v2/galleries/23456"))
        self.assertEqual(34567, Nhentai.extract_gallery_id("34567"))

    def test_headers_include_api_key_when_configured(self):
        Nhentai.api_key = "secret"
        Nhentai.user_agent = "MangaManager/test"

        self.assertEqual({
            "User-Agent": "MangaManager/test",
            "Authorization": "Key secret",
        }, Nhentai._get_headers())

    @patch("ExternalSources.MetadataSources.Providers.Nhentai.requests.get")
    def test_maps_gallery_response_to_comicinfo(self, mock_get):
        mock_get.return_value = _response(data={
            "title": {
                "pretty": "Pretty Title",
                "english": "English Title",
                "japanese": "Japanese Title",
            },
            "upload_date": 1704067200,
            "num_pages": 42,
            "tags": [
                {"type": "tag", "name": "full color"},
                {"type": "tag", "name": "sole male"},
                {"type": "category", "name": "doujinshi"},
                {"type": "character", "name": "character name"},
                {"type": "group", "name": "group name"},
                {"type": "artist", "name": "artist name"},
            ],
        })
        partial = ComicInfo()
        partial.web = "https://nhentai.net/g/12345/"

        cinfo = Nhentai.get_cinfo(partial)

        self.assertEqual("Pretty Title", cinfo.series)
        self.assertEqual("Japanese Title", cinfo.localized_series)
        self.assertEqual("full color, sole male", cinfo.tags)
        self.assertEqual("doujinshi", cinfo.genre)
        self.assertEqual("character name", cinfo.characters)
        self.assertEqual("group name", cinfo.series_group)
        self.assertEqual("artist name", cinfo.writer)
        self.assertEqual("artist name", cinfo.penciller)
        self.assertEqual("artist name", cinfo.cover_artist)
        self.assertEqual(42, cinfo.page_count)
        self.assertEqual(2024, cinfo.year)
        self.assertEqual(1, cinfo.month)
        self.assertEqual(1, cinfo.day)
        self.assertEqual("https://nhentai.net/g/12345/", cinfo.web)
        self.assertEqual(AgeRating.ADULTS_ONLY_18.value, cinfo.age_rating)

    @patch("ExternalSources.MetadataSources.Providers.Nhentai.requests.get")
    def test_404_raises_manga_not_found(self, mock_get):
        mock_get.return_value = _response(status_code=404)
        partial = ComicInfo()
        partial.web = "12345"

        with self.assertRaises(MangaNotFoundError):
            Nhentai.get_cinfo(partial)

    @patch("ExternalSources.MetadataSources.Providers.Nhentai.requests.get")
    def test_429_sets_rate_limit_error(self, mock_get):
        mock_get.return_value = _response(status_code=429)
        partial = ComicInfo()
        partial.web = "12345"

        self.assertIsNone(Nhentai.get_cinfo(partial))
        self.assertEqual("message.nhentai_rate_limit_title", Nhentai.last_error_title_key)

    @patch("ExternalSources.MetadataSources.Providers.Nhentai.requests.get")
    def test_network_error_sets_error(self, mock_get):
        mock_get.side_effect = requests.RequestException()
        partial = ComicInfo()
        partial.web = "12345"

        self.assertIsNone(Nhentai.get_cinfo(partial))
        self.assertEqual("message.nhentai_network_title", Nhentai.last_error_title_key)

    def test_missing_id_sets_error(self):
        partial = ComicInfo()

        self.assertIsNone(Nhentai.get_cinfo(partial))
        self.assertEqual("message.nhentai_missing_id_title", Nhentai.last_error_title_key)


if __name__ == "__main__":
    unittest.main()
