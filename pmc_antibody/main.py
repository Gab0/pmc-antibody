#!/bin/python
#
from typing import Any, Dict, List

import argparse
import sys
import os
import time

import jellyfish
import pandas as pd

from .benchmark import target
from .query import querystring, europepmc, discover_pattern

from .query.querystring import AntibodyInformation


def build_antibody_query(ab):
    queries = querystring.generate_query(ab)

    if not queries:
        return None

    queries = list(set(queries))
    for q in queries:
        print(q)

    query = querystring.build_final_query(queries)

    print(f"Final query has {len(query)}/1500 characters.")
    print(query)

    return query


def execute_search(search_query: str, max_pages: int = 20) -> europepmc.SearchResult:
    result = europepmc.get_articles(search_query)
    print(f"Found {result.hit_count} articles.")

    result.expand_all(max_pages)

    return result


def search_antibody(antibody_identifier: str, max_pages: int = 20):
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

    search_query = build_antibody_query(ab)

    return execute_search(search_query, max_pages)


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

    benchmark_message = "1-indexed antibody number, respecting the .xlsx table names."

    parser.add_argument(
        "-i",
        type=int,
        default=1,
        help=benchmark_message + " To evaluate a single antibody."
    )

    parser.add_argument(
        "-q",
        "--evaluate-queries",
        type=int,
        help=benchmark_message +
        " To evaluate individual queries for a single antibody."

    )
    parser.add_argument(
        "-p",
        "--retrieve-patterns",
        type=int,
        help=benchmark_message +
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

    parser.add_argument(
        "-m",
        "--max-pages-benchmark",
        type=int,
        help="How many pages of results to download when benchmarking search results."
    )

    parser.add_argument(
        "-r",
        "--resume",
        action="store_true",
        help="Whether to resume a previously broken benchmark analysis."
    )

    return parser.parse_args()


def retrieve_patterns(arguments, antibodies):
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
            print(
                discover_pattern.construct_query_pattern_from_regex_match(
                    ab_search_cues,
                    detected_pattern
                )
            )


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

    antibodies = target.benchmark_antibodies()

    if arguments.evaluate_all:
        OUTPUT_PATH = "results.csv"
        results = []

        ABs = list(enumerate(antibodies))
        #ABs = reversed(list(ABs))

        initial_index = 0
        if arguments.resume:
            try:
                resumed_dataset = pd.read_csv(OUTPUT_PATH)
                initial_index = len(resumed_dataset)
            except FileNotFoundError:
                pass

        for idx, ab in ABs[initial_index:]:
            dataset = target.load_dataset(str(idx + 1))
            result = benchmark_antibody(ab, dataset)
            results.append(result)

            # Write entire results on each new row! (safer);
            df = pd.DataFrame(results).round(2)
            if initial_index:
                df = pd.concat([resumed_dataset, df])

            df.to_csv(OUTPUT_PATH, index=None)

    elif arguments.retrieve_patterns:
        retrieve_patterns(arguments, antibodies)

    elif arguments.search_antibody:
        search_antibody(arguments.search_antibody)

    elif arguments.evaluate_queries:
        dataset_index = ensure_sane_dataset_index(arguments.evaluate_queries, len(antibodies))

        ab = antibodies[dataset_index]

        benchmark_dataset = target.load_dataset(str(arguments.evaluate_queries))

        benchmark_individual_queries(ab, benchmark_dataset)

    else:
        dataset_index = ensure_sane_dataset_index(arguments.i, len(antibodies))

        ab = antibodies[dataset_index]

        benchmark_dataset = target.load_dataset(str(arguments.i))

        benchmark_antibody(ab, benchmark_dataset)


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


def benchmark_individual_queries(
        ab: AntibodyInformation,
        benchmark_dataset: pd.DataFrame
) -> Dict[str, Any]:
    """
    Runs searches for PMC queries, but one small query at a time.

    """

    queries = list(set(querystring.generate_query(ab)))

    for q, query in enumerate(queries):
        identifier = f"{ab.get_identifier()}_Q{q + 1}"

        print(f"Searching query: |{query}|")

        benchmark_search_query(
            query,
            identifier,
            benchmark_dataset
        )


def benchmark_antibody(ab: AntibodyInformation, dataset: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs a search for a single antibody and compare against the benchmark.
    Returns a dict containing evaluation metrics.

    """

    ab_identifier = ab.get_identifier()
    search_query = build_antibody_query(ab)

    return benchmark_search_query(search_query, ab_identifier, dataset)


def benchmark_search_query(
        search_query: str,
        search_identifier: str,
        benchmark_dataset: pd.DataFrame
) -> Dict[str, Any]:

    search_result = execute_search(search_query, max_pages=40)

    matched_results = []
    matched_articles = []
    unmatched_articles = []

    verbose = False

    # Mark articles that are from PMC;
    benchmark_dataset.loc[:, "Found"] = [0 for _ in benchmark_dataset.index]
    benchmark_dataset.loc[:, "IS_PMC"] = [target.is_url_pmc(url) for url in benchmark_dataset.URL]
    benchmark_dataset.loc[:, "IS_NOT_PREPRINT"] = [not target.is_url_preprint(url) for url in benchmark_dataset.URL]

    # Match search results with benchmark;
    #
    # This can take a while,
    # depending on the number of results.
    # This is mostly due to our title comparison algorithm,
    t0 = time.time()
    for a, found_article in enumerate(search_result.results):

        if a < 1000:
            try:
                if found_article.pmcid:
                    download_result = "NO ARTICLE"
                    if europepmc.retrieve_article_content(found_article.pmcid):
                        download_result = "OK"
            except AttributeError as e:
                download_result = f"NO ID {e}"

            with open(f"{search_identifier}.txt", 'a', encoding="utf-8") as f:
                f.write(download_result + "\n")

        matched = False
        for b, benchmark_article in enumerate(benchmark_dataset.iloc()):
            if strings_equivalent(found_article.title, benchmark_article.Title):
                matched = True
                benchmark_dataset.loc[b, "Found"] += 1
                break

        if not matched:
            unmatched_articles.append(found_article)
        matched_results.append(matched)

    print(f"Took {round(time.time() - t0)} seconds to evaluate metrics.")

    # Calculate success metrics;
    try:
        agreement_rate = sum(matched_results) / len(matched_results)
        false_positive_rate = 1 - agreement_rate
    except ZeroDivisionError:
        agreement_rate = 0
        false_positive_rate = 0

    fulfillment_rate = calculate_fulfillment_rate(benchmark_dataset)
    fulfillment_pmc_rate = calculate_fulfillment_rate(
        benchmark_dataset[benchmark_dataset.IS_PMC]
    )
    fulfillment_no_preprint_rate = calculate_fulfillment_rate(
        benchmark_dataset[benchmark_dataset.IS_NOT_PREPRINT]
    )

    record = {
        "Antibody ID": search_identifier,
        "Fulfillment Rate": percentage(fulfillment_rate),
        "Fulfillment rate NO-PREPRINT": percentage(fulfillment_no_preprint_rate),
        "Fulfillment rate PMC": percentage(fulfillment_pmc_rate),
        "False Positive Rate": percentage(false_positive_rate),
        "Search Hit Count": search_result.hit_count,
        "Search N": len(search_result.results),
        "Agreement N": sum(matched_results),
        "Benchmark N (CiteAB)": len(benchmark_dataset),
    }

    # Write output records;
    write_article_list(search_identifier, "unmatched-articles", unmatched_articles)
    BENCHMARK_DIRECTORY = "article-benchmark"
    if not os.path.isdir(BENCHMARK_DIRECTORY):
        os.mkdir(BENCHMARK_DIRECTORY)
    benchmark_filepath = os.path.join(
        BENCHMARK_DIRECTORY,
        f"{search_identifier}-benchmark.csv"
    )
    benchmark_dataset.to_csv(benchmark_filepath, index=None)

    show_statistics(record)

    return record


def calculate_fulfillment_rate(benchmark_dataset: pd.DataFrame) -> float:
    try:
        return sum([min(k, 1) for k in benchmark_dataset.Found]) / len(benchmark_dataset)
    except ZeroDivisionError:
        return 0


def show_statistics(record: Dict[str, Any]):
    print("\n")
    for k, v in record.items():
        print(f"{k}: {v}")
    print("\n")


def percentage(rate: float) -> str:
    return f"{round(rate * 100, 2)}%"


if __name__ == "__main__":
    main()
