import json
from pathlib import Path

from knowledge_agent.semantic_retriever import (
    semantic_search,
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

EVALUATION_FILE = (
    PROJECT_ROOT
    / "Testing"
    / "retrieval_eval.json"
)


# ============================================================
# LOAD EVALUATION DATA
# ============================================================

def load_evaluation_dataset():

    if not EVALUATION_FILE.exists():

        raise FileNotFoundError(
            f"Evaluation dataset not found: "
            f"{EVALUATION_FILE}"
        )

    with open(
        EVALUATION_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(value):

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace("_", " ")
    )


# ============================================================
# CHECK IF RESULT MATCHES EXPECTATION
# ============================================================

def result_matches_expected(
    result,
    test_case,
):

    expected_title = normalize_text(
        test_case.get("expected_title")
    )

    expected_section = normalize_text(
        test_case.get("expected_section")
    )

    acceptable_sections = [
        normalize_text(section)
        for section in test_case.get(
            "acceptable_sections",
            []
        )
    ]

    actual_title = normalize_text(
        result.get("title")
    )

    actual_section = normalize_text(
        result.get("section")
    )

    # ----------------------------
    # TITLE CHECK
    # ----------------------------

    title_match = (
        not expected_title
        or actual_title == expected_title
    )

    # ----------------------------
    # SECTION CHECK
    # ----------------------------

    if acceptable_sections:

        section_match = (
            actual_section
            in acceptable_sections
        )

    elif expected_section:

        section_match = (
            actual_section
            == expected_section
        )

    else:

        section_match = True

    return (
        title_match
        and section_match
    )


# ============================================================
# RUN EVALUATION
# ============================================================

def run_evaluation(
    top_k=3,
    threshold=0.65,
):

    test_cases = load_evaluation_dataset()

    total_tests = len(test_cases)

    positive_tests = 0
    negative_tests = 0

    top1_correct = 0
    top3_correct = 0

    no_match_correct = 0
    false_positives = 0
    false_negatives = 0

    failures = []

    print("=" * 80)

    print(
        "IPL SEMANTIC RETRIEVAL EVALUATION"
    )

    print("=" * 80)

    print(
        "Total tests:",
        total_tests
    )

    print(
        "Threshold:",
        threshold
    )

    print(
        "Top-K:",
        top_k
    )

    print("=" * 80)

    for test_case in test_cases:

        test_id = test_case["id"]

        question = test_case["question"]

        expected_match = (
            test_case.get(
                "expected_match",
                True,
            )
        )

        category = test_case.get(
            "category",
            "unknown",
        )

        # Analytics tests are routing tests,
        # not semantic retrieval tests.
        expected_route = test_case.get(
            "expected_route"
        )

        if expected_route == "analytics":

            print(
                f"\nSKIP {test_id}: "
                f"Analytics routing test"
            )

            continue

        print("\n" + "-" * 80)

        print(
            f"{test_id} | {category}"
        )

        print(
            "QUESTION:",
            question
        )

        results = semantic_search(
            question=question,
            top_k=top_k,
            threshold=threshold,
        )

        # ====================================================
        # NEGATIVE / NO-MATCH TEST
        # ====================================================

        if not expected_match:

            negative_tests += 1

            if not results:

                no_match_correct += 1

                print(
                    "RESULT: PASS"
                )

                print(
                    "EXPECTED: NO MATCH"
                )

                print(
                    "ACTUAL: NO MATCH"
                )

            else:

                false_positives += 1

                best = results[0]

                print(
                    "RESULT: FAIL"
                )

                print(
                    "EXPECTED: NO MATCH"
                )

                print(
                    "ACTUAL:",
                    best["title"],
                    "|",
                    best["section"],
                    "|",
                    round(
                        best["score"],
                        4,
                    ),
                )

                failures.append(
                    {
                        "id": test_id,
                        "question": question,
                        "reason":
                            "False positive",
                        "actual_title":
                            best["title"],
                        "actual_section":
                            best["section"],
                        "score":
                            best["score"],
                    }
                )

            continue

        # ====================================================
        # POSITIVE RETRIEVAL TEST
        # ====================================================

        positive_tests += 1

        if not results:

            false_negatives += 1

            print(
                "RESULT: FAIL"
            )

            print(
                "EXPECTED:",
                test_case.get(
                    "expected_title"
                ),
                "|",
                test_case.get(
                    "expected_section"
                ),
            )

            print(
                "ACTUAL: NO MATCH"
            )

            failures.append(
                {
                    "id": test_id,
                    "question": question,
                    "reason":
                        "False negative",
                }
            )

            continue

        # ====================================================
        # TOP-1 CHECK
        # ====================================================

        top1_match = result_matches_expected(
            results[0],
            test_case,
        )

        if top1_match:
            top1_correct += 1

        # ====================================================
        # TOP-3 CHECK
        # ====================================================

        top3_match = any(
            result_matches_expected(
                result,
                test_case,
            )
            for result in results
        )

        if top3_match:
            top3_correct += 1

        # ====================================================
        # PRINT RESULT
        # ====================================================

        print(
            "EXPECTED:",
            test_case.get(
                "expected_title"
            ),
            "|",
            test_case.get(
                "expected_section"
            ),
        )

        print(
            "TOP RESULTS:"
        )

        for rank, result in enumerate(
            results,
            start=1,
        ):

            print(
                f"  {rank}. "
                f'{result["title"]} | '
                f'{result["section"]} | '
                f'{result["score"]:.4f}'
            )

        if top1_match:

            print(
                "RESULT: PASS (TOP-1)"
            )

        elif top3_match:

            print(
                "RESULT: PASS (TOP-3)"
            )

        else:

            print(
                "RESULT: FAIL"
            )

            failures.append(
                {
                    "id": test_id,
                    "question": question,
                    "reason":
                        "Expected chunk not in "
                        "Top-K",
                    "expected_title":
                        test_case.get(
                            "expected_title"
                        ),
                    "expected_section":
                        test_case.get(
                            "expected_section"
                        ),
                    "actual_top1":
                        results[0]["title"],
                    "actual_section":
                        results[0]["section"],
                    "score":
                        results[0]["score"],
                }
            )

    # ========================================================
    # METRICS
    # ========================================================

    top1_accuracy = (
        top1_correct
        / positive_tests
        * 100
        if positive_tests
        else 0
    )

    top3_accuracy = (
        top3_correct
        / positive_tests
        * 100
        if positive_tests
        else 0
    )

    no_match_accuracy = (
        no_match_correct
        / negative_tests
        * 100
        if negative_tests
        else 0
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 80)

    print(
        "EVALUATION SUMMARY"
    )

    print("=" * 80)

    print(
        f"Total dataset cases: {total_tests}"
    )

    print(
        f"Retrieval positive tests: "
        f"{positive_tests}"
    )

    print(
        f"No-match tests: "
        f"{negative_tests}"
    )

    print()

    print(
        f"Top-1 correct: "
        f"{top1_correct}/"
        f"{positive_tests}"
    )

    print(
        f"Top-1 accuracy: "
        f"{top1_accuracy:.2f}%"
    )

    print()

    print(
        f"Top-3 correct: "
        f"{top3_correct}/"
        f"{positive_tests}"
    )

    print(
        f"Top-3 accuracy: "
        f"{top3_accuracy:.2f}%"
    )

    print()

    print(
        f"No-match correct: "
        f"{no_match_correct}/"
        f"{negative_tests}"
    )

    print(
        f"No-match accuracy: "
        f"{no_match_accuracy:.2f}%"
    )

    print()

    print(
        "False positives:",
        false_positives
    )

    print(
        "False negatives:",
        false_negatives
    )

    # ========================================================
    # FAILURES
    # ========================================================

    if failures:

        print("\n" + "=" * 80)

        print(
            "FAILED CASES"
        )

        print("=" * 80)

        for failure in failures:

            print(
                "\nID:",
                failure["id"]
            )

            print(
                "QUESTION:",
                failure["question"]
            )

            print(
                "REASON:",
                failure["reason"]
            )

            if (
                "expected_title"
                in failure
            ):

                print(
                    "EXPECTED:",
                    failure.get(
                        "expected_title"
                    ),
                    "|",
                    failure.get(
                        "expected_section"
                    ),
                )

            if (
                "actual_title"
                in failure
            ):

                print(
                    "ACTUAL:",
                    failure.get(
                        "actual_title"
                    ),
                    "|",
                    failure.get(
                        "actual_section"
                    ),
                )

            if "score" in failure:

                print(
                    "SCORE:",
                    round(
                        failure["score"],
                        4,
                    ),
                )

    else:

        print(
            "\nAll retrieval tests passed."
        )

    return {
        "total_tests":
            total_tests,

        "positive_tests":
            positive_tests,

        "negative_tests":
            negative_tests,

        "top1_accuracy":
            top1_accuracy,

        "top3_accuracy":
            top3_accuracy,

        "no_match_accuracy":
            no_match_accuracy,

        "false_positives":
            false_positives,

        "false_negatives":
            false_negatives,

        "failures":
            failures,
    }


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_evaluation(
        top_k=3,
        threshold=0.65,
    )
