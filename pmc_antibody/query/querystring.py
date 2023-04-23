#!/bin/python
#

from typing import Dict, List, Optional

import itertools
import re
import sys

# NOTE: This list could be loaded from a list instead;
_QUERY_STYLES = """
$SKU $MANUFACTURER
#$TARGET*$CLONE
#$MANUFACTURER AND $CLONE
#$SKU AND $MANUFACTURER
"$TARGET \(Clone #$CLONE, $MANUFACTURER"
"$TARGET antibody \($CLONE; $MANUFACTURER"
"$MANUFACTURER clone $CLONE"
"$MANUFACTURER, clone $CLONE"
"""

QUERY_STYLES = list(filter(None, _QUERY_STYLES.split("\n")))


class AntibodyInformation():
    """ Input information for a single antibody. """
    sku: Optional[str]
    clone_id: Optional[str]
    manufacturer: Optional[str]

    def __init__(self, sku=None, clone_id=None, manufacturer=None, target=None):
        self.sku = sku
        self.clone_id = clone_id
        self.manufacturer = manufacturer
        self.target = target


def vary_manufacturer(manufacturer):
    """
    Takes a manufacturer string and create variations on it.

    Example: 'Bio Rad' can be represented as 'Bio-Rad', 'BioRad' or 'Bio Rad'.

    """

    manufacturer = manufacturer.replace("-", " ")
    fragments = manufacturer.split(" ")

    # -- Generate name variations;
    variations = [
        "-".join(fragments),
        " ".join(fragments),
        "".join(fragments)
    ]

    # -- Ensure unique elements;
    return list(set(variations))


def replace_query_style(ab, style) -> List[str]:

    if style.startswith("#"):
        return []

    patterns: Dict[str, List[str]] = {
        "TARGET": [ab.target],
        "CLONE": [ab.clone_id],
        "MANUFACTURER": vary_manufacturer(ab.manufacturer),
        "SKU": [ab.sku]
    }

    styles = [style]

    for pattern, values in patterns.items():
        if None in values:
            if pattern in style:
                return []
            continue

        # NOTE: This segment is quite complex:
        #
        # If a replaceable pattern contains more than one replacing value,
        # the size of the styles list will be multiplied
        # by the number of replacing values.
        #
        # That's because we need o account
        # for all possible combinations of replaced values!
        new_styles = []
        for value in values:
            new_styles += [
                style.replace(f"${pattern}", value)
                for style in styles
            ]

        styles = new_styles

    # Check if there are any '$PATTERN' in the styles that was not replaced.
    # This would indicate an incompatible style pattern.
    if any(re.findall(r"\$\w+", s) for s in styles):
        print(f"Invalid style pattern; {style}")
        sys.exit(1)

    return styles


def generate_query(ab: AntibodyInformation) -> List[str]:
    """
    Takes information about a single antibody and build multiple queries that
    can retrieve it;
    """

    return list(itertools.chain.from_iterable([
        replace_query_style(ab, style)
        for style in QUERY_STYLES
    ]))


def build_final_query(queries: List[str]) -> str:

    def format_query(query):
        return f'({query})'

    return " OR ".join(map(format_query, queries))
