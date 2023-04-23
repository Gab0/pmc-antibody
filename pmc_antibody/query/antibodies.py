#!/bin/python

import io

import requests
import pandas as pd

BASE_URL = "https://scicrunch.org/php/data-federation-csv.php"

API_KEY = "q8Z8mJPSK7ZZnPOcD5Z5shukSR3dWu9U"


def call_database(query: str):

    parameters = {
        "orMultiFacets": "true",
        "count": "10",
        "nifid": "nif-0000-07730-1",
        "exportType": "data",
        "q": query
    }

    response = requests.get(
        BASE_URL,
        params=parameters,
        headers={
            'User-Agent':
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
    }
    )

    if response.ok:
        print(dir(response))
        print(response.raw.read())
        print(response.reason)
        buf = io.StringIO(response.text)

        return pd.read_csv(buf)


if __name__ == '__main__':
    call_database("anti-bovine CD4 (Clone #CC8, BioRad, Hercules, CA)")
