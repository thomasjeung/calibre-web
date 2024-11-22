# -*- coding: utf-8 -*-

#  This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.

# Daum Books api documentation: https://developers.kakao.com/docs/latest/ko/daum-search/dev-guide
from typing import Dict, List, Optional
from urllib.parse import quote
from datetime import datetime

import requests

from cps import logger
from cps.isoLanguages import get_lang3, get_language_name
from cps.services.Metadata import MetaRecord, MetaSourceInfo, Metadata

log = logger.create()


class Daum(Metadata):
    __name__ = "Daum"
    __id__ = "daum"
    DESCRIPTION = "Daum Books"
    META_URL = "https://search.daum.net/search?w=bookpage"
    SEARCH_URL = "https://dapi.kakao.com/v3/search/book?target=title&query="
    
    # def __init__(self, api_key: str) -> None:
    #     super().__init__()
    #     self.api_key = api_key

    def search(
        self, query: str, generic_cover: str = "", locale: str = "en"
    ) -> Optional[List[MetaRecord]]:
        val = list()
        if self.active:
            title_tokens = list(self.get_title_tokens(query, strip_joiners=False))
            if title_tokens:
                tokens = [quote(t.encode("utf-8")) for t in title_tokens]
                query = "+".join(tokens)
            try:
                headers = {'Authorization': f'KakaoAK {APIKEY}'}
                results = requests.get(Daum.SEARCH_URL + query, headers=headers)
                results.raise_for_status()
            except Exception as e:
                log.warning(e)
                return None
            for result in results.json().get("documents", []):
                val.append(
                    self._parse_search_result(
                        result=result, generic_cover=generic_cover, locale=locale
                    )
                )
        return val

    def _parse_search_result(
        self, result: Dict, generic_cover: str, locale: str
    ) -> MetaRecord:
        isbn_numbers = result.get("isbn", "").split()
        isbn_13 = isbn_numbers[1] if len(isbn_numbers) > 1 else ""

        match = MetaRecord(
            id=isbn_13,  # using ISBN_13 as ID if available
            title=result["title"],
            authors=result.get("authors", []),
            url=result["url"],
            source=MetaSourceInfo(
                id=self.__id__,
                description=Daum.DESCRIPTION,
                link=Daum.META_URL,
            ),
        )

        match.cover = result.get("thumbnail", generic_cover)
        match.description = result.get("contents", "")
        match.languages = self._parse_languages(result=result, locale=locale)
        match.publisher = result.get("publisher", "")
        try:
            match.publishedDate = datetime.strptime(result.get("datetime", ""), "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
        except ValueError:
            match.publishedDate = ""
        match.rating = 0  # Daum API does not provide ratings
        match.series, match.series_index = "", 1
        match.tags = []

        match.identifiers = {"daum": isbn_13, "isbn": isbn_13}
        return match

    @staticmethod
    def _parse_languages(result: Dict, locale: str) -> List[str]:
        # Assuming Daum Books are mostly in Korean, override if necessary
        languages = [get_language_name(locale, get_lang3("ko"))]
        return languages
