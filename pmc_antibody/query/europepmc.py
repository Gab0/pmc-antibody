#!/bin/python
"""
Methods to query EuropePMC search endpoints.
"""

from typing import Dict, Optional, Union
import math
import os
import time

import requests


BASE_URL = "https://www.ebi.ac.uk"


class Article():
    """ Information on a single article. """
    def __init__(self, article_json):

        mandatory_fields = [
            "title",
            "id",
            "source",
        ]

        self.id_fields = [
            "pmid",
            "pmcid",
            "doi"
        ]

        for v in mandatory_fields:
            self.__dict__[v] = article_json[v]


        # NOTE: Mostly for debug purposes;
        self.article_json = article_json

    def get_id(self) -> Optional[str]:
        for v in self.id_fields:
            try:
                return  self.article_json[v]
            except KeyError:
                pass

        return None


class SearchResult():
    """ Information on a single EuropePMC search result. """
    def __init__(self, result_json, parameters):
        self.hit_count = result_json["hitCount"]

        self.parameters = parameters
        self.results = []

        self.update(result_json)

    def update(self, result_json):
        self.results += [
            Article(article)
            for article in result_json["resultList"]["result"]
        ]

        try:
            next_cursor_mark = result_json["nextCursorMark"]
        except KeyError:
            next_cursor_mark = None

        try:
            self.next_cursor_mark = next_cursor_mark if next_cursor_mark != self.next_cursor_mark else None
        except AttributeError:
            self.next_cursor_mark = next_cursor_mark

        # NOTE: Mostly for debug purposes;
        self.result_json = result_json

    def next_page(self):

        self.parameters.update({
            "cursorMark": self.next_cursor_mark
        })

        result_json = search_articles(self.parameters)

        self.update(result_json)

    def expand_all(self, max_pages):
        page = 2
        while self.next_cursor_mark is not None and page < max_pages:

            result_max_pages = math.ceil(self.hit_count / 100)
            current_max_pages = min(result_max_pages, max_pages)
            print(f"Retrieving next page of search results... {page}/{current_max_pages + 1}: {self.next_cursor_mark}")

            self.next_page()

            # NOTE: Rate limit to avoid bans;
            time.sleep(0.1)
            page += 1


def get_annotations(query: str):
    """ NOTE: How to call this endpoint? Gives 400: Bad Request"""

    parameters = {
        "entity": query,
        "pageSize": 8
    }

    URL = BASE_URL + "/europepmc/annotations_api/annotationsByArticleIds"


def get_articles(query: str) -> SearchResult:
    """ Do a single article search on EuropePMC. """
    parameters: Dict[str, Union[str, int]] = {
        "query": query,
        "format": "json",
        "pageSize": 100
    }

    return SearchResult(search_articles(parameters), parameters)


def search_articles(parameters):
    URL = BASE_URL + "/europepmc/webservices/rest/search"
    response = requests.get(
        URL,
        params=parameters
    )

    return response.json()



def retrieve_article_content(article_id: str) -> Optional[str]:
    """
    Retrieve the full text XML for a single article.
    The article cache is also managed here, so we only download an article once.

    """

    ARTICLE_CACHE_DIRECTORY = "articles"

    if not os.path.isdir(ARTICLE_CACHE_DIRECTORY):
        os.mkdir(ARTICLE_CACHE_DIRECTORY)

    cache_filepath = os.path.join(ARTICLE_CACHE_DIRECTORY, f"{article_id}.xml")

    try:
        with open(cache_filepath, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        pass

    URL = BASE_URL + f"/europepmc/webservices/rest/{article_id}/fullTextXML"

    result = requests.get(URL)

    if result.ok:
        xml_content = result.text

        with open(cache_filepath, 'w', encoding="utf-8") as f:
            f.write(xml_content)

        return xml_content

    return None
