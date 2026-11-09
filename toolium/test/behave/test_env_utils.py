"""
Copyright 2023 Telefónica Investigación y Desarrollo, S.A.U.
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

from unittest import mock

import pytest

from toolium.behave.env_utils import (
    ACTIONS_AFTER_FEATURE,
    ACTIONS_AFTER_SCENARIO,
    ACTIONS_BEFORE_FEATURE,
    ACTIONS_BEFORE_SCENARIO,
    DynamicEnvironment,
)


@pytest.fixture
def context():
    context = mock.MagicMock()
    return context


@pytest.fixture
def dyn_env():
    dyn_env = DynamicEnvironment()
    dyn_env.actions[ACTIONS_BEFORE_FEATURE] = ['Given before feature step']
    dyn_env.actions[ACTIONS_BEFORE_SCENARIO] = ['Given before scenario step']
    dyn_env.actions[ACTIONS_AFTER_SCENARIO] = ['Then after scenario step']
    dyn_env.actions[ACTIONS_AFTER_FEATURE] = ['Then after feature step']
    return dyn_env


# TODO: add tests for get_steps_from_feature_description method


def test_execute_before_feature_steps_without_actions(context):
    # Create dynamic environment without actions
    dyn_env = DynamicEnvironment()

    dyn_env.execute_before_feature_steps(context)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is False
    context.execute_steps.assert_not_called()
    context.feature.mark_skipped.assert_not_called()


def test_execute_before_feature_steps_passed_actions(context, dyn_env):
    dyn_env.execute_before_feature_steps(context)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is False
    context.execute_steps.assert_called_with('Given before feature step')
    context.feature.mark_skipped.assert_not_called()


def test_execute_before_feature_steps_failed_actions(context, dyn_env):
    context.execute_steps.side_effect = Exception('Exception in before feature step')
    dyn_env.get_feature_scenarios_to_fail = mock.MagicMock(return_value=[context.scenario])
    dyn_env.fail_scenarios_first_step = mock.MagicMock()

    dyn_env.execute_before_feature_steps(context)
    assert dyn_env.feature_error is True
    assert dyn_env.scenario_error is False
    context.execute_steps.assert_called_with('Given before feature step')
    context.feature.mark_skipped.assert_called_once_with()
    # Scenarios must be collected before marking the feature as skipped and failed after
    dyn_env.get_feature_scenarios_to_fail.assert_called_once_with(context)
    dyn_env.fail_scenarios_first_step.assert_called_once_with(
        context,
        [context.scenario],
        context.execute_steps.side_effect,
    )


def test_execute_before_feature_steps_failed_actions_order(context, dyn_env):
    """Scenarios must be collected before the feature is marked as skipped, because mark_skipped makes
    should_run return False for all the scenarios."""
    context.execute_steps.side_effect = Exception('Exception in before feature step')
    manager = mock.MagicMock()
    manager.get_feature_scenarios_to_fail = mock.MagicMock()
    manager.mark_skipped = mock.MagicMock()
    manager.fail_scenarios_first_step = mock.MagicMock()
    dyn_env.get_feature_scenarios_to_fail = manager.get_feature_scenarios_to_fail
    dyn_env.fail_scenarios_first_step = manager.fail_scenarios_first_step
    context.feature.mark_skipped = manager.mark_skipped

    dyn_env.execute_before_feature_steps(context)

    assert [call[0] for call in manager.mock_calls] == [
        'get_feature_scenarios_to_fail',
        'mark_skipped',
        'fail_scenarios_first_step',
    ]


def test_get_feature_scenarios_to_fail(context, dyn_env):
    runnable = mock.MagicMock()
    skipped_by_tags = mock.MagicMock()
    runnable.should_run.return_value = True
    skipped_by_tags.should_run.return_value = False
    context.feature.walk_scenarios.return_value = [runnable, skipped_by_tags]

    scenarios = dyn_env.get_feature_scenarios_to_fail(context)

    assert scenarios == [runnable]
    runnable.should_run.assert_called_once_with(context.config)


def test_fail_scenarios_first_step(context, dyn_env):
    scenario_with_steps = mock.MagicMock()
    scenario_with_steps.steps = [mock.MagicMock()]
    scenario_with_steps.background_steps = []
    scenario_with_background = mock.MagicMock()
    scenario_with_background.steps = [mock.MagicMock()]
    scenario_with_background.background_steps = [mock.MagicMock()]
    dyn_env.fail_first_step_precondition_exception = mock.MagicMock()

    dyn_env.fail_scenarios_first_step(context, [scenario_with_steps, scenario_with_background], 'error message')

    assert dyn_env.fail_first_step_precondition_exception.call_count == 2
    dyn_env.fail_first_step_precondition_exception.assert_any_call(scenario_with_steps, 'error message')
    dyn_env.fail_first_step_precondition_exception.assert_any_call(scenario_with_background, 'error message')
    context.logger.warning.assert_called_once_with('Background from scenario status udpated to fail')


def test_execute_before_scenario_steps_without_actions(context):
    # Create dynamic environment without actions
    dyn_env = DynamicEnvironment()

    dyn_env.execute_before_scenario_steps(context)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is False
    context.execute_steps.assert_not_called()
    context.scenario.mark_skipped.assert_not_called()


def test_execute_before_scenario_steps_passed_actions(context, dyn_env):
    dyn_env.execute_before_scenario_steps(context)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is False
    context.execute_steps.assert_called_with('Given before scenario step')
    context.scenario.mark_skipped.assert_not_called()


def test_execute_before_scenario_steps_failed_actions(context, dyn_env):
    context.execute_steps.side_effect = Exception('Exception in before scenario step')

    dyn_env.execute_before_scenario_steps(context)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is True
    context.execute_steps.assert_called_with('Given before scenario step')
    context.scenario.mark_skipped.assert_called_once_with()


def test_execute_after_scenario_steps_without_actions(context):
    # Create dynamic environment without actions
    dyn_env = DynamicEnvironment()
    dyn_env.fail_first_step_precondition_exception = mock.MagicMock()

    dyn_env.execute_after_scenario_steps(context)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is False
    context.execute_steps.assert_not_called()
    context.scenario.reset.assert_not_called()
    dyn_env.fail_first_step_precondition_exception.assert_not_called()


def test_execute_after_scenario_steps_passed_actions(context, dyn_env):
    dyn_env.fail_first_step_precondition_exception = mock.MagicMock()

    dyn_env.execute_after_scenario_steps(context)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is False
    context.execute_steps.assert_called_with('Given after scenario step')
    context.scenario.reset.assert_not_called()
    dyn_env.fail_first_step_precondition_exception.assert_not_called()


def test_execute_after_scenario_steps_failed_actions(context, dyn_env):
    context.execute_steps.side_effect = Exception('Exception in after scenario step')
    dyn_env.fail_first_step_precondition_exception = mock.MagicMock()

    dyn_env.execute_after_scenario_steps(context)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is False
    context.execute_steps.assert_called_with('Given after scenario step')
    context.scenario.reset.assert_not_called()
    dyn_env.fail_first_step_precondition_exception.assert_not_called()


def test_execute_after_scenario_steps_failed_before_scenario(context, dyn_env):
    # Before scenario step fails
    dyn_env.scenario_error = True
    dyn_env.before_error_message = 'Exception in before scenario step'
    dyn_env.fail_first_step_precondition_exception = mock.MagicMock()

    with pytest.raises(Exception) as excinfo:  # noqa: PT011
        dyn_env.execute_after_scenario_steps(context)
    assert 'Before scenario steps have failed: Exception in before scenario step' == str(excinfo.value)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is False
    assert dyn_env.before_error_message is None
    context.execute_steps.assert_called_with('Given after scenario step')
    context.scenario.reset.assert_called()
    dyn_env.fail_first_step_precondition_exception.assert_called()


def test_execute_after_scenario_steps_failed_actions_failed_before_scenario(context, dyn_env):
    # Before scenario step fails
    dyn_env.scenario_error = True
    dyn_env.before_error_message = 'Exception in before scenario step'
    context.execute_steps.side_effect = Exception('Exception in after scenario step')
    dyn_env.fail_first_step_precondition_exception = mock.MagicMock()

    with pytest.raises(Exception) as excinfo:  # noqa: PT011
        dyn_env.execute_after_scenario_steps(context)
    assert 'Before scenario steps have failed: Exception in before scenario step' == str(excinfo.value)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is False
    assert dyn_env.before_error_message is None
    context.execute_steps.assert_called_with('Given after scenario step')
    context.scenario.reset.assert_called()
    dyn_env.fail_first_step_precondition_exception.assert_called()


def test_execute_after_feature_steps_without_actions(context):
    # Create dynamic environment without actions
    dyn_env = DynamicEnvironment()
    dyn_env.fail_first_step_precondition_exception = mock.MagicMock()

    dyn_env.execute_after_feature_steps(context)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is False
    context.execute_steps.assert_not_called()
    context.feature.reset.assert_not_called()
    dyn_env.fail_first_step_precondition_exception.assert_not_called()


def test_execute_after_feature_steps_passed_actions(context, dyn_env):
    dyn_env.fail_first_step_precondition_exception = mock.MagicMock()

    dyn_env.execute_after_feature_steps(context)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is False
    context.execute_steps.assert_called_with('Given after feature step')
    context.feature.reset.assert_not_called()
    dyn_env.fail_first_step_precondition_exception.assert_not_called()


def test_execute_after_feature_steps_failed_actions(context, dyn_env):
    context.execute_steps.side_effect = Exception('Exception in after feature step')
    dyn_env.fail_first_step_precondition_exception = mock.MagicMock()

    dyn_env.execute_after_feature_steps(context)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is False
    context.execute_steps.assert_called_with('Given after feature step')
    context.feature.reset.assert_not_called()
    dyn_env.fail_first_step_precondition_exception.assert_not_called()


def test_execute_after_feature_steps_failed_before_feature(context, dyn_env):
    # Before feature step fails
    dyn_env.feature_error = True
    dyn_env.before_error_message = 'Exception in before feature step'
    dyn_env.fail_first_step_precondition_exception = mock.MagicMock()
    context.feature.walk_scenarios.return_value = [context.scenario]

    with pytest.raises(Exception) as excinfo:  # noqa: PT011
        dyn_env.execute_after_feature_steps(context)
    assert 'Before feature steps have failed: Exception in before feature step' == str(excinfo.value)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is False
    assert dyn_env.before_error_message is None
    context.execute_steps.assert_called_with('Given after feature step')
    context.feature.reset.assert_called_once_with()
    dyn_env.fail_first_step_precondition_exception.assert_called_once_with(
        context.scenario,
        'Exception in before feature step',
    )


def test_execute_after_feature_steps_failed_actions_failed_before_feature(context, dyn_env):
    # Before feature step fails
    dyn_env.feature_error = True
    dyn_env.before_error_message = 'Exception in before feature step'
    dyn_env.fail_first_step_precondition_exception = mock.MagicMock()
    context.execute_steps.side_effect = Exception('Exception in after feature step')
    context.feature.walk_scenarios.return_value = [context.scenario]

    with pytest.raises(Exception) as excinfo:  # noqa: PT011
        dyn_env.execute_after_feature_steps(context)
    assert 'Before feature steps have failed: Exception in before feature step' == str(excinfo.value)
    assert dyn_env.feature_error is False
    assert dyn_env.scenario_error is False
    assert dyn_env.before_error_message is None
    context.execute_steps.assert_called_with('Given after feature step')
    context.feature.reset.assert_called_once_with()
    dyn_env.fail_first_step_precondition_exception.assert_called_once_with(
        context.scenario,
        'Exception in before feature step',
    )


def test_fail_first_step_precondition_exception(dyn_env):
    scenario = mock.MagicMock()
    step1 = mock.MagicMock()
    step2 = mock.MagicMock()
    scenario.steps = [step1, step2]
    dyn_env.before_error_message = 'Exception in before feature step'

    dyn_env.fail_first_step_precondition_exception(scenario, dyn_env.before_error_message)
    assert step1.status == 'failed'
    assert str(step1.exception) == 'Preconditions failed'
    assert step1.error_message == 'Exception in before feature step'


def test_fail_first_step_precondition_exception_without_steps(dyn_env):
    scenario = mock.MagicMock()
    scenario.steps = []
    dyn_env.before_error_message = 'Exception in before feature step'

    dyn_env.fail_first_step_precondition_exception(scenario, dyn_env.before_error_message)
