# -*- coding: utf-8 -*-
"""
Copyright 2025 Telefónica Innovación Digital, S.L.
This file is part of Toolium.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import functools
import re
from behave.model import ScenarioOutline
from behave.model_core import Status


def get_accuracy_and_retries_from_tags(tags):
    """
    Extract accuracy and retries values from accuracy tag using regex.
    Examples of valid tags:
    - accuracy
    - accuracy_90
    - accuracy_percent_90
    - accuracy_90_10
    - accuracy_percent_90_retries_10

    :param tags: behave tags
    :return: dict with 'accuracy' and 'retries' keys if tag matches, None otherwise
    """
    accuracy_regex = re.compile(r'^accuracy(?:_(?:percent_)?(\d+)(?:_retries_(\d+)|_(\d+))?)?', re.IGNORECASE)
    for tag in tags:
        match = accuracy_regex.search(tag)
        if match:
            # Default values: 90% accuracy, 10 retries
            accuracy_percent = (int(match.group(1)) / 100.0) if match.group(1) else 0.9
            # Check if retries is in group 2 (accuracy_percent_90_retries_10) or group 3 (accuracy_90_10)
            retries = int(match.group(2)) if match.group(2) else (int(match.group(3)) if match.group(3) else 10)
            return {'accuracy': accuracy_percent, 'retries': retries}
    return None


def patch_scenario_with_accuracy(context, scenario, accuracy=0.9, retries=10):
    """Monkey-patches :func:`~behave.model.Scenario.run()` to execute multiple times and calculate the accuracy of the
    results.

    This is helpful when the test is flaky due to unreliable test infrastructure or when the application under test is
    AI based and its responses may vary slightly.

    :param context: behave context
    :param scenario: Scenario or ScenarioOutline to patch
    :param accuracy: Minimum accuracy required to consider the scenario as passed
    :param retries: Number of times the scenario will be executed
    """
    def scenario_run_with_accuracy(context, scenario_run, scenario, *args, **kwargs):
        # Execute the scenario multiple times and count passed executions
        passed_executions = 0
        for retry in range(1, retries+1):
            if not scenario_run(*args, **kwargs):
                passed_executions += 1
                status = "PASSED"
            else:
                status = "FAILED"
            print(f"ACCURACY SCENARIO {status}: retry {retry}/{retries}")
            context.logger.info(f"Accuracy scenario {status} (retry {retry}/{retries})")

        # Calculate scenario accuracy
        scenario_accuracy = passed_executions / retries
        has_passed = scenario_accuracy >= accuracy
        final_status = 'PASSED' if has_passed else 'FAILED'
        print(f"\nACCURACY SCENARIO {final_status}: {retries} retries, accuracy {scenario_accuracy} >= {accuracy}")
        final_message = (f"Accuracy scenario {final_status} after {retries} retries with"
                         f" accuracy {scenario_accuracy} >= {accuracy}")

        # Set final scenario status
        if has_passed:
            context.logger.info(final_message)
            scenario.set_status(Status.passed)
        else:
            context.logger.error(final_message)
            scenario.set_status(Status.failed)
        return not has_passed  # Run method returns true when failed

    scenario_run = scenario.run
    scenario.run = functools.partial(scenario_run_with_accuracy, context, scenario_run, scenario)


def patch_scenario_from_tags(context, scenario):
    """Patch scenario with accuracy method when accuracy tags are present in scenario.

    :param context: behave context
    :param scenario: behave scenario
    """
    accuracy_data = get_accuracy_and_retries_from_tags(scenario.effective_tags)
    if accuracy_data:
        patch_scenario_with_accuracy(context, scenario, accuracy=accuracy_data['accuracy'],
                                     retries=accuracy_data['retries'])


def patch_feature_scenarios_with_accuracy(context, feature):
    """Patch feature scenarios with accuracy method when accuracy tags are present in scenarios.

    :param context: behave context
    :param feature: behave feature
    """
    try:
        for scenario in feature.scenarios:
            if isinstance(scenario, ScenarioOutline):
                for outline_scenario in scenario.scenarios:
                    patch_scenario_from_tags(context, outline_scenario)
            else:
                patch_scenario_from_tags(context, scenario)
    except Exception as e:
        # Log error but do not fail the execution to avoid errors in before feature method
        context.logger.error(f"Error applying accuracy policy: {e}")
