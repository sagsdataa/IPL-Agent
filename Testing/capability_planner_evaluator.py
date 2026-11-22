import json
import time
from pathlib import Path

from agent.capability_planner import (
    CapabilityPlannerError,
    create_capability_plan,
)


# ============================================================
# CONFIGURATION
# ============================================================

REQUESTS_PER_BATCH = 10
BATCH_PAUSE_SECONDS = 65


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
    / "capability_planner_evaluation.json"
)


# ============================================================
# LOAD DATASET
# ============================================================

def load_evaluation_dataset():

    if not EVALUATION_FILE.exists():

        raise FileNotFoundError(
            "Planner evaluation dataset "
            f"not found: {EVALUATION_FILE}"
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
    )


# ============================================================
# INFRASTRUCTURE ERROR CHECK
# ============================================================

def is_infrastructure_error(
    error,
):

    error_text = str(error).lower()

    infrastructure_patterns = (
        "429",
        "resource_exhausted",
        "quota",
        "503",
        "unavailable",
        "high demand",
    )

    return any(
        pattern in error_text
        for pattern in infrastructure_patterns
    )


# ============================================================
# CAPABILITY CHECK
# ============================================================

def get_actual_capabilities(
    plan,
):

    return [
        task.capability
        for task in plan.tasks
    ]


def capabilities_match(
    actual,
    expected,
):

    return (
        sorted(actual)
        == sorted(expected)
    )


# ============================================================
# DEPENDENCY CHECK
# ============================================================

def get_actual_dependencies(
    plan,
):

    dependencies = {}

    for task in plan.tasks:

        if task.depends_on:

            dependencies[
                task.task_id
            ] = sorted(
                task.depends_on
            )

    return dependencies


def dependencies_match(
    actual,
    expected,
):

    normalized_expected = {
        task_id: sorted(values)
        for task_id, values
        in expected.items()
    }

    return (
        actual
        == normalized_expected
    )


# ============================================================
# ENTITY CHECK
# ============================================================

def entities_match(
    plan,
    expected_entities,
):

    if not expected_entities:
        return True

    actual_entities = {
        (
            normalize_text(
                entity.entity_type
            ),
            normalize_text(
                entity.canonical_name
            ),
        )
        for entity in plan.entities
    }

    for expected in expected_entities:

        expected_entity = (
            normalize_text(
                expected.get(
                    "entity_type"
                )
            ),
            normalize_text(
                expected.get(
                    "canonical_name"
                )
            ),
        )

        if (
            expected_entity
            not in actual_entities
        ):

            return False

    return True


# ============================================================
# TASK QUESTION REQUIREMENTS
# ============================================================

def task_questions_match(
    plan,
    requirements,
):

    if not requirements:
        return True

    for (
        capability_name,
        required_terms,
    ) in requirements.items():

        matching_tasks = [
            task
            for task in plan.tasks
            if (
                task.capability
                == capability_name
            )
        ]

        if not matching_tasks:
            return False

        capability_passed = False

        for task in matching_tasks:

            normalized_question = (
                normalize_text(
                    task.question
                )
            )

            all_terms_found = all(
                normalize_text(term)
                in normalized_question
                for term in required_terms
            )

            if all_terms_found:

                capability_passed = True
                break

        if not capability_passed:
            return False

    return True


# ============================================================
# UNSUPPORTED CHECK
# ============================================================

def unsupported_matches(
    plan,
    expected_unsupported,
):

    if not expected_unsupported:
        return True

    return (
        plan.route == "unsupported"
        and not plan.tasks
        and bool(
            plan.unsupported_reason
        )
    )


# ============================================================
# PERCENTAGE
# ============================================================

def percentage(
    numerator,
    denominator,
):

    if denominator == 0:
        return 100.0

    return (
        numerator
        / denominator
        * 100
    )


# ============================================================
# RUN EVALUATION
# ============================================================

def run_evaluation():

    test_cases = (
        load_evaluation_dataset()
    )

    total = len(test_cases)

    successfully_evaluated = 0
    infrastructure_failures = 0
    valid_plans = 0

    route_correct = 0
    capability_correct = 0
    task_count_correct = 0
    dependency_correct = 0

    entity_correct = 0
    task_question_correct = 0
    unsupported_correct = 0

    entity_test_count = 0
    task_question_test_count = 0
    unsupported_test_count = 0

    planner_failures = []

    print("=" * 80)
    print(
        "IPL CAPABILITY PLANNER EVALUATION"
    )
    print("=" * 80)

    print(
        "Dataset cases:",
        total,
    )

    print("=" * 80)

    # ========================================================
    # TEST LOOP
    # ========================================================

    for index, test_case in enumerate(
        test_cases,
        start=1,
    ):

        # ----------------------------------------------------
        # RATE LIMIT PROTECTION
        # ----------------------------------------------------

        if (
            index > 1
            and (
                (index - 1)
                % REQUESTS_PER_BATCH
                == 0
            )
        ):

            print()
            print("=" * 80)

            print(
                f"Rate-limit pause after "
                f"{index - 1} requests."
            )

            print(
                f"Waiting "
                f"{BATCH_PAUSE_SECONDS} "
                f"seconds..."
            )

            print("=" * 80)

            time.sleep(
                BATCH_PAUSE_SECONDS
            )

        print(
            f"\nProcessing test case "
            f"{index}/{total}..."
        )

        test_id = (
            test_case["id"]
        )

        category = (
            test_case.get(
                "category",
                "unknown",
            )
        )

        question = (
            test_case["question"]
        )

        expected_route = (
            test_case[
                "expected_route"
            ]
        )

        expected_capabilities = (
            test_case.get(
                "expected_capabilities",
                [],
            )
        )

        expected_task_count = (
            test_case.get(
                "expected_task_count",
                0,
            )
        )

        expected_dependencies = (
            test_case.get(
                "expected_dependencies",
                {},
            )
        )

        expected_entities = (
            test_case.get(
                "expected_entities",
                [],
            )
        )

        task_requirements = (
            test_case.get(
                "task_question_requirements",
                {},
            )
        )

        expected_unsupported = (
            test_case.get(
                "expected_unsupported",
                False,
            )
        )

        print(
            "-" * 80
        )

        print(
            f"{test_id} | "
            f"{category}"
        )

        print(
            "QUESTION:",
            question,
        )

        # ----------------------------------------------------
        # CREATE PLAN
        # ----------------------------------------------------

        try:

            plan = create_capability_plan(
                question=question,
                conversation_context={},
            )

            successfully_evaluated += 1
            valid_plans += 1

        except CapabilityPlannerError as error:

            if is_infrastructure_error(
                error
            ):

                infrastructure_failures += 1

                print(
                    "RESULT: NOT EVALUATED "
                    "(MODEL/API UNAVAILABLE)"
                )

                print(
                    "INFRASTRUCTURE ERROR:",
                    error,
                )

                continue

            print(
                "RESULT: FAIL"
            )

            print(
                "PLANNER ERROR:",
                error,
            )

            planner_failures.append(
                {
                    "id":
                        test_id,

                    "question":
                        question,

                    "reason":
                        "Planner error",

                    "details":
                        str(error),
                }
            )

            continue

        # ====================================================
        # ROUTE
        # ====================================================

        route_passed = (
            plan.route
            == expected_route
        )

        if route_passed:
            route_correct += 1


        # ====================================================
        # CAPABILITIES
        # ====================================================

        actual_capabilities = (
            get_actual_capabilities(
                plan
            )
        )

        capability_passed = (
            capabilities_match(
                actual_capabilities,
                expected_capabilities,
            )
        )

        if capability_passed:
            capability_correct += 1


        # ====================================================
        # TASK COUNT
        # ====================================================

        task_count_passed = (
            len(plan.tasks)
            == expected_task_count
        )

        if task_count_passed:
            task_count_correct += 1


        # ====================================================
        # DEPENDENCIES
        # ====================================================

        actual_dependencies = (
            get_actual_dependencies(
                plan
            )
        )

        dependency_passed = (
            dependencies_match(
                actual_dependencies,
                expected_dependencies,
            )
        )

        if dependency_passed:
            dependency_correct += 1


        # ====================================================
        # ENTITIES
        # ====================================================

        entity_passed = True

        if expected_entities:

            entity_test_count += 1

            entity_passed = (
                entities_match(
                    plan,
                    expected_entities,
                )
            )

            if entity_passed:
                entity_correct += 1


        # ====================================================
        # TASK QUESTION QUALITY
        # ====================================================

        task_question_passed = True

        if task_requirements:

            task_question_test_count += 1

            task_question_passed = (
                task_questions_match(
                    plan,
                    task_requirements,
                )
            )

            if task_question_passed:

                task_question_correct += 1


        # ====================================================
        # UNSUPPORTED
        # ====================================================

        unsupported_passed = True

        if expected_unsupported:

            unsupported_test_count += 1

            unsupported_passed = (
                unsupported_matches(
                    plan,
                    True,
                )
            )

            if unsupported_passed:

                unsupported_correct += 1


        # ====================================================
        # CASE RESULT
        # ====================================================

        case_passed = all(
            [
                route_passed,
                capability_passed,
                task_count_passed,
                dependency_passed,
                entity_passed,
                task_question_passed,
                unsupported_passed,
            ]
        )

        print(
            "EXPECTED ROUTE:",
            expected_route,
        )

        print(
            "ACTUAL ROUTE:",
            plan.route,
        )

        print(
            "EXPECTED CAPABILITIES:",
            expected_capabilities,
        )

        print(
            "ACTUAL CAPABILITIES:",
            actual_capabilities,
        )

        print(
            "EXPECTED TASK COUNT:",
            expected_task_count,
        )

        print(
            "ACTUAL TASK COUNT:",
            len(plan.tasks),
        )

        print(
            "EXPECTED DEPENDENCIES:",
            expected_dependencies,
        )

        print(
            "ACTUAL DEPENDENCIES:",
            actual_dependencies,
        )

        for task in plan.tasks:

            print(
                f"{task.task_id}: "
                f"{task.capability} | "
                f"{task.question} | "
                f"depends_on="
                f"{task.depends_on}"
            )

        if case_passed:

            print(
                "RESULT: PASS"
            )

            continue

        print(
            "RESULT: FAIL"
        )

        failure_reasons = []

        if not route_passed:

            failure_reasons.append(
                "route"
            )

        if not capability_passed:

            failure_reasons.append(
                "capabilities"
            )

        if not task_count_passed:

            failure_reasons.append(
                "task_count"
            )

        if not dependency_passed:

            failure_reasons.append(
                "dependencies"
            )

        if not entity_passed:

            failure_reasons.append(
                "entities"
            )

        if not task_question_passed:

            failure_reasons.append(
                "task_question_quality"
            )

        if not unsupported_passed:

            failure_reasons.append(
                "unsupported_behavior"
            )

        planner_failures.append(
            {
                "id":
                    test_id,

                "question":
                    question,

                "reason":
                    ", ".join(
                        failure_reasons
                    ),

                "expected_route":
                    expected_route,

                "actual_route":
                    plan.route,

                "expected_capabilities":
                    expected_capabilities,

                "actual_capabilities":
                    actual_capabilities,

                "expected_dependencies":
                    expected_dependencies,

                "actual_dependencies":
                    actual_dependencies,
            }
        )


    # ========================================================
    # CALCULATE METRICS
    # ========================================================

    plan_validity_accuracy = (
        percentage(
            valid_plans,
            successfully_evaluated,
        )
    )

    route_accuracy = (
        percentage(
            route_correct,
            successfully_evaluated,
        )
    )

    capability_accuracy = (
        percentage(
            capability_correct,
            successfully_evaluated,
        )
    )

    task_count_accuracy = (
        percentage(
            task_count_correct,
            successfully_evaluated,
        )
    )

    dependency_accuracy = (
        percentage(
            dependency_correct,
            successfully_evaluated,
        )
    )

    entity_accuracy = (
        percentage(
            entity_correct,
            entity_test_count,
        )
    )

    task_question_accuracy = (
        percentage(
            task_question_correct,
            task_question_test_count,
        )
    )

    unsupported_accuracy = (
        percentage(
            unsupported_correct,
            unsupported_test_count,
        )
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        "\n" + "=" * 80
    )

    print(
        "PLANNER EVALUATION SUMMARY"
    )

    print("=" * 80)

    print(
        f"Dataset cases: "
        f"{total}"
    )

    print(
        f"Successfully evaluated: "
        f"{successfully_evaluated}/"
        f"{total}"
    )

    print(
        f"Infrastructure failures: "
        f"{infrastructure_failures}"
    )

    print()

    print(
        f"Valid plans: "
        f"{valid_plans}/"
        f"{successfully_evaluated} "
        f"({plan_validity_accuracy:.2f}%)"
    )

    print()

    print(
        f"Route accuracy: "
        f"{route_correct}/"
        f"{successfully_evaluated} "
        f"({route_accuracy:.2f}%)"
    )

    print(
        f"Capability accuracy: "
        f"{capability_correct}/"
        f"{successfully_evaluated} "
        f"({capability_accuracy:.2f}%)"
    )

    print(
        f"Task-count accuracy: "
        f"{task_count_correct}/"
        f"{successfully_evaluated} "
        f"({task_count_accuracy:.2f}%)"
    )

    print(
        f"Dependency accuracy: "
        f"{dependency_correct}/"
        f"{successfully_evaluated} "
        f"({dependency_accuracy:.2f}%)"
    )

    print(
        f"Entity accuracy: "
        f"{entity_correct}/"
        f"{entity_test_count} "
        f"({entity_accuracy:.2f}%)"
    )

    print(
        f"Task-question accuracy: "
        f"{task_question_correct}/"
        f"{task_question_test_count} "
        f"({task_question_accuracy:.2f}%)"
    )

    print(
        f"Unsupported accuracy: "
        f"{unsupported_correct}/"
        f"{unsupported_test_count} "
        f"({unsupported_accuracy:.2f}%)"
    )


    # ========================================================
    # PLANNER FAILURES
    # ========================================================

    if planner_failures:

        print(
            "\n" + "=" * 80
        )

        print(
            "GENUINE PLANNER FAILURES"
        )

        print("=" * 80)

        for failure in planner_failures:

            print()

            print(
                "ID:",
                failure["id"],
            )

            print(
                "QUESTION:",
                failure["question"],
            )

            print(
                "REASON:",
                failure["reason"],
            )

            if (
                "expected_route"
                in failure
            ):

                print(
                    "EXPECTED ROUTE:",
                    failure[
                        "expected_route"
                    ],
                )

                print(
                    "ACTUAL ROUTE:",
                    failure[
                        "actual_route"
                    ],
                )

            if (
                "details"
                in failure
            ):

                print(
                    "DETAILS:",
                    failure[
                        "details"
                    ],
                )

    else:

        print()

        print(
            "No genuine planner "
            "failures detected."
        )


    # ========================================================
    # INFRASTRUCTURE NOTE
    # ========================================================

    if infrastructure_failures:

        print(
            "\n" + "=" * 80
        )

        print(
            "INFRASTRUCTURE NOTE"
        )

        print("=" * 80)

        print(
            f"{infrastructure_failures} "
            f"case(s) were excluded from "
            f"planner-quality metrics because "
            f"the model/API was unavailable."
        )


    # ========================================================
    # RETURN METRICS
    # ========================================================

    return {

        "total_cases":
            total,

        "successfully_evaluated":
            successfully_evaluated,

        "infrastructure_failures":
            infrastructure_failures,

        "valid_plan_accuracy":
            plan_validity_accuracy,

        "route_accuracy":
            route_accuracy,

        "capability_accuracy":
            capability_accuracy,

        "task_count_accuracy":
            task_count_accuracy,

        "dependency_accuracy":
            dependency_accuracy,

        "entity_accuracy":
            entity_accuracy,

        "task_question_accuracy":
            task_question_accuracy,

        "unsupported_accuracy":
            unsupported_accuracy,

        "failures":
            planner_failures,
    }


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_evaluation()