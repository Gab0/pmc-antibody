#!/bin/python
""" Install script for PMC-Antibody. """

from setuptools import setup, find_packages

entry_points = {
    "console_scripts": [
        "pmcab=pmc_antibody.main:main",
    ]
}

setup(
    name="pmc-antibody",
    version="0.333",
    description="Antibody citation search engine.",
    packages=find_packages(),
    platforms='any',
    entry_points=entry_points,
    package_data={
        "": [
            "citeab_output.xlsx"
        ]
    }
)
