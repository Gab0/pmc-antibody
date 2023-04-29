#!/bin/python
from typing import List, Optional

import re
import os

import pandas as pd


def load_dataset(sheet_name: str):

    # FIXME: There are better ways o load this;
    dataset_path = os.path.join(
        os.path.dirname(__file__),
        "citeab_output.xlsx"
    )

    dataset = pd.read_excel(
        dataset_path,
        sheet_name=sheet_name,
        skiprows=4
    )

    return dataset


def extract_all_ids(df: pd.DataFrame) -> List[str]:
    """ """
    def extract_link(link: str) -> List[str]:
        return re.findall(r"PMC[0-9]+", link)

    ids = []
    for link in df["URL"]:
        if isinstance(link, str):
            ids += extract_link(link)

    return ids


def is_url_pmc(url: str) -> bool:
    if not isinstance(url, str):
        return False

    if "europepmc.org" in url:
        return True

    return False
