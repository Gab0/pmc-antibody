#!/bin/python

from typing import List

import re

from . import querystring

ESCAPE_CHARS = False


def discover_antibody_pattern(ab):
    patterns = generate_regex_patterns(ab)

    for pattern in patterns:
        pass


def generate_regex_patterns(ab) -> List[str]:
    wildcard = ".{0,16}"

    pattern_seeds = [
        [ab.sku, ab.manufacturer],
        [ab.clone_id, ab.manufacturer],
        [ab.target, ab.sku]
    ]

    patterns = []
    for pattern_seed in pattern_seeds:
        for transformer in [lambda x: x, reversed]:
            pattern = wildcard.join(transformer(pattern_seed))
            patterns.append(pattern)

    return patterns


def construct_query_pattern_from_regex_match(ab_search_cues, regex_match: str) -> str:
    """
    Transforms matched string that is specific
    to a certain antibody into a generic search pattern.

    """

    for wildcard, rep_set in ab_search_cues.items():
        for rep in rep_set:
            if rep is not None:
                regex_match = regex_match.replace(rep, f"${wildcard}")

    if ESCAPE_CHARS:
        must_be_escaped_chars = "().{}"

        for c in must_be_escaped_chars:
            regex_match = regex_match.replace(c, f"\\{c}")

    return regex_match


def run_patterns_on_article(regex_patterns: List[str], xml_content: str) -> List[str]:
    results = []
    for regex_pattern in regex_patterns:
        try:
            results += re.findall(regex_pattern, xml_content)
        except re.error as e:
            print(regex_pattern)
            print(e)

    return results
