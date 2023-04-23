#!/bin/python

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

