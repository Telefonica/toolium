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

import csv
import datetime
import functools
import os
import re
from copy import deepcopy

from behave.model import ScenarioOutline
from behave.model_core import Status

from toolium.driver_wrappers_pool import DriverWrappersPool


def get_accuracy_and_executions_from_tags(tags, accuracy_data_len=None):
    """
    Extract accuracy and executions values from accuracy tags

    Examples of valid tags:

    - accuracy
    - accuracy_90
    - accuracy_percent_90
    - accuracy_90_10
    - accuracy_percent_90_executions_10

    :param tags: behave tags
    :param accuracy_data_len: length of accuracy data if available
    :return: dict with 'accuracy' and 'executions' keys if tag matches, None otherwise
    """
    # Default values: 90% accuracy, 10 executions
    default_accuracy = 0.9
    default_executions = accuracy_data_len if accuracy_data_len is not None else 10
    accuracy_regex = re.compile(
        r'^accuracy(?!_data)(?:_(?:percent_)?(\d+)(?:_executions_(\d+)|_(\d+))?)?$',
        re.IGNORECASE,
    )
    for tag in tags:
        match = accuracy_regex.search(tag)
        if match:
            accuracy_percent = (int(match.group(1)) / 100.0) if match.group(1) else default_accuracy
            # Check if executions is in group 2 (accuracy_percent_90_executions_10) or group 3 (accuracy_90_10)
            executions = (
                int(match.group(2))
                if match.group(2)
                else (int(match.group(3)) if match.group(3) else default_executions)
            )
            return {'accuracy': accuracy_percent, 'executions': executions}
    return None


def get_accuracy_data_suffix_from_tags(tags):
    """
    Extract accuracy data suffix from accuracy_data tags

    Examples of valid tags:
    - accuracy_data
    - accuracy_data_suffix

    :param tags: behave tags
    :return: data_key_suffix if tag matches, empty string otherwise
    """
    accuracy_data_regex = re.compile(r'^accuracy_data(?:_(\w+))?', re.IGNORECASE)
    for tag in tags:
        match = accuracy_data_regex.search(tag)
        if match:
            return f'_{match.group(1)}' if match.group(1) else ''
    return ''


def patch_scenario_with_accuracy(context, scenario, data_key_suffix, accuracy=0.9, executions=10):
    """Monkey-patches :func:`~behave.model.Scenario.run()` to execute multiple times and calculate the accuracy of the
    results.

    This is helpful when the test is flaky due to unreliable test infrastructure or when the application under test is
    AI based and its responses may vary slightly.

    :param context: behave context
    :param scenario: Scenario or ScenarioOutline to patch
    :param data_key_suffix: suffix to identify accuracy data in context storage
    :param accuracy: minimum accuracy required to consider the scenario as passed
    :param executions: number of times the scenario will be executed
    """

    def scenario_run_with_accuracy(context, scenario_run, scenario, *args, **kwargs):
        # Execute the scenario multiple times and count passed executions
        passed_executions = skipped_executions = 0
        results = []

        # Copy scenario steps to avoid modifications in each execution, especially when using behave variables
        # transformation, like map_param and replace_param methods
        orig_steps = deepcopy(scenario.steps)
        for execution in range(executions):
            context.logger.info('Running accuracy scenario execution (%d/%d)', execution + 1, executions)
            # Store execution data in context
            store_execution_data(context, execution, data_key_suffix)
            # Restore original steps before each execution
            scenario.steps = deepcopy(orig_steps)

            # Run scenario
            scenario_result = scenario_run(*args, **kwargs)

            # Store and log execution result
            if scenario_result:
                status = 'FAILED'
            elif scenario.status == Status.skipped:
                skipped_executions += 1
                status = 'SKIPPED'
            else:
                passed_executions += 1
                status = 'PASSED'
            results.append(
                {
                    'data': context.storage['accuracy_execution_data'],
                    'status': status,
                    'message': get_error_message_from_scenario(scenario),
                },
            )
            print(f'ACCURACY SCENARIO {status}: execution {execution + 1}/{executions}')  # noqa: T201
            context.logger.info('Accuracy scenario execution %s (%d/%d)', status, execution + 1, executions)

        # Save results to CSV file
        save_accuracy_results_to_csv(context, scenario, results)

        if executions == skipped_executions:
            run_response = False  # Run method returns true only when failed
            context.logger.info('All accuracy scenario executions are skipped')
        else:
            # Calculate scenario accuracy
            scenario_accuracy = passed_executions / (executions - skipped_executions)
            has_passed = scenario_accuracy >= accuracy
            run_response = not has_passed  # Run method returns true only when failed
            final_status = 'PASSED' if has_passed else 'FAILED'
            print(  # noqa: T201
                f'\nACCURACY SCENARIO {final_status}: {executions} executions,'
                f' accuracy {scenario_accuracy} >= {accuracy}',
            )
            final_message = (
                f'Accuracy scenario {final_status} after {executions} executions with'
                f' accuracy {scenario_accuracy} >= {accuracy}'
                f' ({passed_executions} passed, {skipped_executions} skipped,'
                f' {executions - passed_executions - skipped_executions} failed)'
            )

            # Set final scenario status
            if has_passed:
                context.logger.info(final_message)
                scenario.set_status(Status.passed)
            else:
                context.logger.error(final_message)
                scenario.set_status(Status.failed)
                scenario.exception = AssertionError(final_message)

        # Clean accuracy execution data from context
        context.storage.pop('accuracy_execution_data', None)
        context.storage.pop('accuracy_execution_index', None)

        after_accuracy_scenario(context, scenario)

        return run_response

    scenario_run = scenario.run
    scenario.run = functools.partial(scenario_run_with_accuracy, context, scenario_run, scenario)


def patch_scenario_from_tags(context, scenario):
    """Patch scenario with accuracy method when accuracy tags are present in scenario.

    :param context: behave context
    :param scenario: behave scenario
    """
    data_key_suffix = get_accuracy_data_suffix_from_tags(scenario.effective_tags)
    accuracy_data = get_accuracy_data(context, data_key_suffix)
    accuracy_data_len = len(accuracy_data) if accuracy_data else None
    accuracy_settings = get_accuracy_and_executions_from_tags(scenario.effective_tags, accuracy_data_len)
    if accuracy_settings:
        patch_scenario_with_accuracy(
            context,
            scenario,
            data_key_suffix,
            accuracy=accuracy_settings['accuracy'],
            executions=accuracy_settings['executions'],
        )


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
        context.logger.error('Error applying accuracy policy: %s', e)


def get_accuracy_data(context, data_key_suffix):
    """
    Retrieve accuracy data stored in context.

    :param context: behave context
    :param data_key_suffix: suffix to identify accuracy data in context storage
    :return: accuracy data list
    """
    accuracy_data_key = f'accuracy_data{data_key_suffix}'
    accuracy_data = context.storage.get(accuracy_data_key, [])
    assert isinstance(accuracy_data, list), f'Expected {accuracy_data_key} must be a list: {accuracy_data}'
    return accuracy_data


def store_execution_data(context, execution, data_key_suffix):
    """Extract data to be used in current execution and store it in accuracy_execution_data key in context.
    context.storage['accuracy_data{data_key_suffix}'] is expected to be a list of dicts with data for each execution.
    Execution data is selected using modulo to avoid index errors, so executions can be greater than available data.

    :param context: behave context
    :param execution: current execution index
    :param data_key_suffix: suffix to identify accuracy data in context storage
    """
    accuracy_data = get_accuracy_data(context, data_key_suffix)
    execution_data = accuracy_data[execution % len(accuracy_data)] if accuracy_data else None
    context.storage['accuracy_execution_data'] = execution_data
    context.storage['accuracy_execution_index'] = execution
    context.logger.info(
        'Stored accuracy data for execution %d in accuracy_execution_data: %s',
        execution + 1,
        execution_data,
    )


def after_accuracy_scenario(context, scenario):
    """Hook called after accuracy scenario execution.
    Monkey-patch this method to implement custom behavior after accuracy scenario execution, like calling Allure
    after_scenario method.

    :param context: behave context
    :param scenario: behave scenario
    """
    pass


def get_error_message_from_scenario(scenario):
    """
    Extract error message from failed scenario.

    :param scenario: behave scenario
    :return: error message string
    """
    if scenario.exception:
        return str(scenario.exception)
    for step in scenario.steps:
        if step.status == Status.failed:
            return str(step.exception)
    return ''


def save_accuracy_results_to_csv(context, scenario, results):
    """
    Save accuracy test results to a CSV file.

    :param context: behave context
    :param scenario: behave scenario
    :param results: list of execution results
    """
    # Create output directory if it doesn't exist
    output_dir = os.path.join(DriverWrappersPool.output_directory, 'accuracy')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Generate filename with timestamp and scenario info
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    scenario_name = scenario.name.replace(' ', '_').replace(',', '')
    csv_filename = f'{output_dir}/results_{scenario_name}_{timestamp}.csv'

    # Write execution results to file
    try:
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Execution data', 'Status', 'Message'])
            for result in results:
                csv_writer.writerow([result['data'], result['status'], result['message']])
        context.logger.info('Accuracy results saved to: %s', csv_filename)
    except Exception as e:
        context.logger.error('Error saving accuracy results to CSV: %s', e)
