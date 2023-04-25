#!/bin/python
#
from typing import Any, Dict

import argparse
import sys

import jellyfish
import pandas as pd

from .query import querystring, europepmc

from .benchmark.false_positive import load_dataset


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

    return europepmc.get_articles(query)


def write_unmatched_article_list(identifier: str, unmatched_articles) -> None:

    records = []
    for article in unmatched_articles:
        record = {
            "Title": article.title,
            "ID": article.uid
        }
        records.append(record)

    filepath = f"{identifier}-false-positives.csv"
    pd.DataFrame(records).to_csv(filepath, index=None)


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i",
        type=int,
        default=1,
        help="1-indexed antibody number, respecting the .xlsx table names. To evaluate a single antibody."
    )

    parser.add_argument(
        "-r",
        "--retrieve-patterns",
        type=int,
        help="1-indexed antibody target, respecting the .xlsx table names. To scrape search patterns for a single antibody."
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

    antibodies = [
        querystring.AntibodyInformation("550280", "RM4-5", "BD Biosciences", "CD4"),
        querystring.AntibodyInformation("11-0041-82", "GK1.5", "Invitrogen", "CD4"),
        querystring.AntibodyInformation("ab183685", "EPR19514", "Abcam", "CD4"),
        querystring.AntibodyInformation("100401", "GK1.5", "BioLegend", "CD4"),
        querystring.AntibodyInformation("ab133616", "EPR6855", "Abcam", "CD4"),
        querystring.AntibodyInformation("AF1828", None, "R&D Systems", "TREM2"),
        querystring.AntibodyInformation("BAF1828", None, "R&D Systems", "TREM2")
        # querystring.AntibodyInformation("MCA1653F", "CC8", "Bio Rad", "CD4"),
        # querystring.AntibodyInformation("9102", None, "Cell Signaling Technology", "p44/42 MAPK")
    ]

    if arguments.evaluate_all:
        results = []

        for idx, ab in enumerate(antibodies):
            dataset = load_dataset(str(idx + 1))
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

        for target_article_id in target_article_ids:
            print(target_article_id, end="")
            xml_content = europepmc.retrieve_article_content(target_article_id)
            if xml_content is None:
                print("!")
                continue
            print()
            detected_patterns = discover_pattern.run_patterns_on_article(regex_patterns, xml_content)

            for detected_pattern in detected_patterns:
                print(discover_pattern.construct_query_pattern_from_regex_match(ab_search_cues, detected_pattern))

    elif arguments.search_antibody:
        search_antibody(arguments.search_antibody)

    else:
        dataset_index = arguments.i - 1

        if dataset_index < 0 or dataset_index >= len(antibodies):
            print("Invalid dataset index.")
            sys.exit(1)

        ab = antibodies[arguments.i - 1]

        dataset = load_dataset(str(arguments.i))

        benchmark_antibody(ab, dataset)


def benchmark_antibody(ab: querystring.AntibodyInformation, dataset: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs a search for a single antibody and compare against the benchmark.
    Returns a dict containing evaluation metrics.

    """

    ab_identifier = f"{ab.sku}/{ab.manufacturer}"
    search_result = process_antibody(ab)

    matched_results = []
    matched_articles = []
    unmatched_articles = []
    verbose = False

    for found_article in search_result.results:
        matched = False
        for benchmark_title in dataset.Title:
            delta = jellyfish.levenshtein_distance(
                found_article.title,
                benchmark_title
            )
            if delta < 0.15:
                if delta > 0:
                    print("Not exact match:")
                    print(found_article.title)
                    print(benchmark_title)
                    print()
                matched = True
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

    print("\n")
    for k, v in record.items():
        print(f"{k}: {v}")
    print("\n")

    return record


def percentage(rate: float) -> str:
    return f"{round(rate * 100, 2)}%"


if __name__ == "__main__":
    main()
