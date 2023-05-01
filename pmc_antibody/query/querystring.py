#!/bin/python
#

from typing import Dict, List, Optional, Union

import itertools
import re
import sys

# NOTE: This list could be loaded from a separate file instead;
_QUERY_STYLES = """
$SKU $MANUFACTURER

$TARGET Clone #$CLONE, $MANUFACTURER
$TARGET antibody $CLONE; $MANUFACTURER

#$TARGET, 1:100; #$SKU
#$TARGET, 1:75; #$SKU
#$TARGET, 1:50; #$SKU
$TARGET, 1:25; #$SKU

$TARGET Cat # $SKU

$TARGET $SKU

("anti-$TARGET ($CLONE)" AND "$MANUFACTURER")
("anti-$TARGET Clone $CLONE" AND "$MANUFACTURER")
("$TARGET Ab \\(clone $CLONE" AND "$MANUFACTURER")

#$TARGET-V500 ($CLONE

$MANUFACTURER clone $CLONE

$MANUFACTURER $SKU

("clone $CLONE" AND "$MANUFACTURER")

$CLONE $MANUFACTURER
$CLONE

"$CLONE anti-$TARGET"

$SKU), and $TARGET
#$SKU, L3T4; $MANUFACTURER

#$CLONE, IgG2a, $MANUFACTURER

cat. $SKU
Cat#$SKU
Cat. No. $SKU
/$SKU
; #$SKU

"""


def format_query_pattern(query: str) -> str:
    if query.startswith('"') or query.startswith('("'):
        return query

    return f'"{query}"'


QUERY_STYLES = [
    format_query_pattern(query)
    for query in _QUERY_STYLES.split("\n")
    if query.strip() and not query.startswith("#")
]


class AntibodyInformation():
    """ Input information for a single antibody. """
    sku: Optional[str]
    clone_id: Optional[str]
    manufacturer: Optional[Union[List[str], str]]

    def __init__(self, sku=None, clone_id=None, manufacturer=None, target=None):
        self.sku = sku
        self.clone_id = clone_id
        self.manufacturer = manufacturer
        self.target = target

    def get_identifier(self) -> str:
        manufacturer = self.manufacturer
        if isinstance(self.manufacturer, list):
            manufacturer = self.manufacturer[0]

        return f"{manufacturer}:{self.sku}"


def expand_term(term: Union[List[str], str, None]):
    """
    Takes a term string and create variations on it.

    Example: 'Bio Rad' can be represented as 'Bio-Rad', 'BioRad' or 'Bio Rad'.

    """

    # If term is already provided as a list, leave it as it is;
    if isinstance(term, list):
        return term

    if term is None:
        return [None]

    term = term.replace("-", " ")
    fragments = term.split(" ")

    # -- Generate name variations;
    variations = [
        "-".join(fragments),
        " ".join(fragments),
        "".join(fragments)
    ]

    # -- Ensure unique elements;
    return list(set(variations))


def expand_clone_name(term: Union[List[str], str, None]):
    """
    Takes a clone name and create variations on it.

    Example: 'RM4-5' can be represented as 'RM4.5' or even 'RM 4-5'.

    """

    # If term is already provided as a list, leave it as it is;
    if isinstance(term, list):
        return term

    if term is None:
        return [None]

    variations = [
        term,
        term.replace("-", "."),
        term.replace(".", "-"),
        re.sub(r"(\w)(\d)", r"\1 \2", term),
        re.sub(r"(\d)(\w)", r"\1 \2", term)
    ]

    return list(set(variations))


def variable_search_cues(ab: AntibodyInformation) -> Dict[str, List[str]]:

    return {
        "TARGET": [ab.target],
        "CLONE": expand_clone_name(ab.clone_id),
        "MANUFACTURER": expand_term(ab.manufacturer),
        "SKU": [ab.sku]
    }


def replace_query_style(ab, style) -> List[str]:

    patterns = variable_search_cues(ab)

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

    def _format_query(query):
        return f'({query})'

    def format_query(query):
        return query

    return " OR ".join(map(format_query, queries))
