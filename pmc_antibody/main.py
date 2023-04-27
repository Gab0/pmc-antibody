#!/bin/python
#
from typing import Any, Dict

import argparse
import sys

import jellyfish
import pandas as pd

from .benchmark import target
from .query import querystring, europepmc, discover_pattern


def process_antibody(ab):
    queries = querystring.generate_query(ab)

    if not queries:
        return None

    queries = list(set(queries))
    for q in queries:
        print(q)

    query = querystring.build_final_query(queries)

    print(f"Final query has {len(query)}/1500 characters.")
    print(query)

    result = europepmc.get_articles(query)
    result.expand_all(max_pages=20)

    return result


def search_antibody(antibody_identifier):
    """ This is the search function to be called if using this project as a library. """

    identifiers = [
        s.strip() for s in antibody_identifier.split(",")
    ]

    if len(identifiers) == 3:
        manufacturer, sku, ab_target = identifiers
        clone_id = None
    elif len(identifiers == 4):
        manufacturer, sku, clone_id, ab_target = identifiers

    else:
        print(f"Bad antibody identifier: {antibody_identifier}!")
        sys.exit(1)

    ab = querystring.AntibodyInformation(sku, clone_id, manufacturer, ab_target)

    return process_antibody(ab)


def write_article_list(
        ab_identifier: str,
        list_identifier: str,
        articles: List[europepmc.Article]
) -> None:

    ARTICLE_LIST_DIRECTORY = "article-list"
    if not os.path.isdir(ARTICLE_LIST_DIRECTORY):
        os.mkdir(ARTICLE_LIST_DIRECTORY)

    records = []
    for article in articles:
        record = {
            "Title": article.title,
            "ID": article.get_id()
        }
        records.append(record)

    filepath = f"{ab_identifier}-{list_identifier}.csv"
    pd.DataFrame(records).to_csv(
        os.path.join(ARTICLE_LIST_DIRECTORY, filepath),
        index=None
    )


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i",
        type=int,
        default=1,
        help="1-indexed antibody number, respecting the .xlsx table names." +
        " To evaluate a single antibody."
    )

    parser.add_argument(
        "-r",
        "--retrieve-patterns",
        type=int,
        help="1-indexed antibody target, respecting the .xlsx table names." +
        " To scrape search patterns for a single antibody."
    )

    parser.add_argument(
        "-a",
        "--evaluate-all",
        action="store_true",
        help="Evaluate all antibodies and build a metrics table."
    )

    parser.add_argument(
        "-s",
        "--search-antibody",
        type=str,
        help="Antibody identifier to search for. Format:" +
        "'MANUFACTURER,SKU,CLONE,TARGET', where 'CLONE' is optional."
    )

    parser.add_argument(
        "-j",
        "--pattern-jump-to-index",
        type=int,
        help="Jump to a specific reference table index when discovering search patterns."
    )

    return parser.parse_args()


def main():
    """
    This function compares our current search results
    with CiteAB results which are stored in xlsx tables.

    Success metrics:

    1. Number of articles retrieved.
    2. Number of false positives,
       which are retrieved articles that were not found by CietAB.

    """

    arguments = parse_arguments()

    # NOTE: This list matches the antibody order found in the .xlsx reference table;
    antibodies = [
        AntibodyInformation("550280", "RM4-5", ["BD Biosciences", "BD Pharmingen"], "CD4"),
        AntibodyInformation("11-0041-82", "GK1.5", "Invitrogen", "CD4"),
        AntibodyInformation("ab183685", "EPR19514", "Abcam", "CD4"),
        AntibodyInformation("100401", "GK1.5", "BioLegend", "CD4"),
        AntibodyInformation("ab133616", "EPR6855", "Abcam", "CD4"),
        AntibodyInformation("AF1828", None, "R&D Systems", "TREM2"),
        AntibodyInformation("BAF1828", None, "R&D Systems", "TREM2")
        # AntibodyInformation("MCA1653F", "CC8", "Bio Rad", "CD4"),
        # AntibodyInformation("9102", None, "Cell Signaling Technology", "p44/42 MAPK")
    ]

    if arguments.evaluate_all:
        results = []

        for idx, ab in enumerate(antibodies):
            dataset = target.load_dataset(str(idx + 1))
            result = benchmark_antibody(ab, dataset)
            results.append(result)

        df = pd.DataFrame(results).round(2)
        df.to_csv("results.csv", index=None)

    elif arguments.retrieve_patterns:
        dataset_index = ensure_sane_dataset_index(arguments.retrieve_patterns, len(antibodies))
        dataset = target.load_dataset(str(arguments.retrieve_patterns))
        target_article_ids = target.extract_all_ids(dataset)

        ab = antibodies[dataset_index]

        ab_search_cues = querystring.variable_search_cues(ab)

        regex_patterns = discover_pattern.generate_regex_patterns(ab)
        secondary_regex_patterns = discover_pattern.generate_secondary_regex_patterns(ab)

        article_ids_iterable = enumerate(target_article_ids[arguments.pattern_jump_to_index:])
        for idx, target_article_id in article_ids_iterable:

            xml_content = europepmc.retrieve_article_content(target_article_id)

            status = "Ok" if xml_content is not None else "Unreachable"

            message = "\t".join([
                f"{idx + 1}",
                target_article_id,
                status
            ])

            print(message)
            print()

            if xml_content is None:
                continue

            # Detect patterns;
            detected_patterns = discover_pattern.run_patterns_on_article(
                regex_patterns,
                xml_content
            )

            if not detected_patterns:
                detected_patterns = discover_pattern.run_patterns_on_article(
                    secondary_regex_patterns,
                    xml_content
                )

            for detected_pattern in detected_patterns:
                print(discover_pattern.construct_query_pattern_from_regex_match(ab_search_cues, detected_pattern))

    elif arguments.search_antibody:
        search_antibody(arguments.search_antibody)

    else:
        dataset_index = ensure_sane_dataset_index(arguments.i, len(antibodies))

        ab = antibodies[dataset_index]

        dataset = target.load_dataset(str(arguments.i))

        benchmark_antibody(ab, dataset)


def ensure_sane_dataset_index(idx: int, dataset_size: int):

    if idx < 0 or idx >= dataset_size:
        print("Invalid dataset index.")
        sys.exit(1)

    return idx - 1


def strings_equivalent(a: str, b: str) -> bool:
    delta = jellyfish.levenshtein_distance(a, b)

    if delta < 35:
        return True
        # if delta > 0:
        #     print("Not exact match:")
        #     print(found_article.title)
        #     print(benchmark_article.Title)
        #     print()

    return False


def benchmark_antibody(ab: querystring.AntibodyInformation, dataset: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs a search for a single antibody and compare against the benchmark.
    Returns a dict containing evaluation metrics.

    """

    ab_identifier = ab.get_identifier()
    search_result = process_antibody(ab)

    matched_results = []
    matched_articles = []
    unmatched_articles = []

    missed_articles = []

    verbose = False

    dataset["Found"] = [False for _ in dataset.index]

    t0 = time.time()
    for found_article in search_result.results:
        matched = False
        for benchmark_article in dataset.iloc():
            if strings_equivalent(found_article.title, benchmark_article.Title):
                matched = True
                benchmark_article.Found = True
                break
        if not matched:
            unmatched_articles.append(found_article)
        matched_results.append(matched)

    agreement_rate = sum(matched_results) / len(matched_results)
    false_positive_rate = 1 - agreement_rate

    fulfillment_rate = sum(matched_results) / len(dataset.Title)

    record = {
        "Antibody ID": ab_identifier,
        "Fulfillment Rate": percentage(fulfillment_rate),
        "False Positive Rate": percentage(false_positive_rate),
        "Search N": search_result.hit_count,
        "Agreement N": sum(matched_results),
        "Benchmark N (CiteAB)": len(dataset),
    }

    write_article_list(ab_identifier, "unmatched-articles", unmatched_articles)

    print("\n")
    for k, v in record.items():
        print(f"{k}: {v}")
    print("\n")

    return record


def percentage(rate: float) -> str:
    return f"{round(rate * 100, 2)}%"


if __name__ == "__main__":
    main()
