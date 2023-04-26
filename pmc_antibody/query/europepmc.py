#!/bin/python
"""
Methods to query EuropePMC search endpoints.
"""

from typing import Dict, Optional, Union
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

        _optional_fields = [
            "pmid",
            "pmcid",
            "doi"
        ]

        for v in mandatory_fields:
            self.__dict__[v] = article_json[v]

        # NOTE: Mostly for debug purposes;
        self.article_json = article_json


class SearchResult():
    """ Information on a single EuropePMC search result. """
    def __init__(self, result_json):
        self.hit_count = result_json["hitCount"]

        self.results = []

        self.update(result_json)

    def update(self, result_json):
        self.results += [
            Article(article)
            for article in result_json["resultList"]["result"]
        ]

        try:
            next_page = result_json["nextPageUrl"]
        except KeyError:
            next_page = None

        self.next_page_url = next_page

        # NOTE: Mostly for debug purposes;
        self.result_json = result_json

    def next_page(self):
        response = requests.get(self.next_page_url)
        result_json = response.json()
        print(self.hit_count)
        self.update(result_json)

        print(self.next_page_url)

    def expand_all(self):
        while self.next_page_url is not None:
            self.next_page()
            time.sleep(1.0)


def get_annotations(query: str):
    """ NOTE: How to call this endpoint? Gives 400: Bad Request"""

    parameters = {
        "entity": query,
        "pageSize": 8
    }

    URL = BASE_URL + "/europepmc/annotations_api/annotationsByArticleIds"


def get_articles(query: str, pageToken=None) -> SearchResult:
    """ Do a single article search on EuropePMC. """
    parameters: Dict[str, Union[str, int]] = {
        "query": query,
        "format": "json",
        "pageSize": 100
    }

    URL = BASE_URL + "/europepmc/webservices/rest/search"
    response = requests.get(
        URL,
        params=parameters
    )

    content = response.json()

    return SearchResult(content)


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
