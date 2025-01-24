# -*- coding: utf-8 -*-
"""
Copyright 2017 Telefónica Investigación y Desarrollo, S.A.U.
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

import sys
import warnings

# Actions types defined in feature files
ACTIONS_BEFORE_FEATURE = 'actions before the feature'
ACTIONS_BEFORE_SCENARIO = 'actions before each scenario'
ACTIONS_AFTER_SCENARIO = 'actions after each scenario'
ACTIONS_AFTER_FEATURE = 'actions after the feature'
# Valid prefix in action steps
KEYWORDS = ['Setup', 'Check', 'Given', 'When', 'Then', 'And', 'But']
GIVEN_PREFIX = 'Given'
TABLE_SEPARATOR = '|'
STEP_TEXT_SEPARATORS = ['"""', "'''"]
EMPTY = ''

warnings.filterwarnings('ignore')


class Logger:
    def __init__(self, logger, show):
        """
        constructor
        :param logger: logger instance
        :param show: determine if messages are displayed by console
        """
        self.logger = logger
        self.show = show

    def warn(self, exc):
        """
        log a warning message:
        :param exc: exception message
        """
        msg = 'trying to execute a step in the environment: \n' \
              '           - Exception: %s' % exc
        if self.logger is not None:
            self.logger.warning(msg)
        self.by_console('      WARN - %s' % msg)

    def error(self, exc):
        """
        log an error message:
        :param exc: exception message
        """
        msg = 'trying to execute a step in the environment: \n' \
              '           - Exception: %s' % exc
        if self.logger is not None:
            self.logger.error(msg)
        self.by_console('      ERROR - %s' % msg)

    def debug(self, value):
        """
        log a debug message
        :param value: text to log
        """
        if self.logger is not None:
            self.logger.debug(value)

    def by_console(self, text_to_print):
        """
        print in console avoiding output buffering
        :param text_to_print: Text to print by console
        """
        if self.show:
            sys.stdout.write("%s\n" % text_to_print)
            sys.stdout.flush()


class DynamicEnvironment:
    """
    This class is useful when we would like execute generic steps: before the feature, before each scenario,
     after the feature or/and after each scenario.
    It is necessary to append certain lines in the environment.py:

        from common.utils.env_utils import DynamicEnvironment


        def before_all(context):
            context.dyn_env = DynamicEnvironment(logger=context.logger)


        def before_feature(context, feature):
            # ---- get all steps defined in the feature description associated to each action ----
            context.dyn_env.get_steps_from_feature_description(context, feature.description)
            # ---- actions before the feature ----
            context.dyn_env.execute_before_feature_steps(context)


        def before_scenario(context, scenario):
            # ---- actions before each scenario ----
            context.dyn_env.execute_before_scenario_steps(context)


        def after_scenario(context, scenario):
            # ---- actions after each scenario ----
            context.dyn_env.execute_after_scenario_steps(context)


        def after_feature(context, feature):
            # ---- actions after feature ----
            context.dyn_env.execute_after_feature_steps(context)

    Error management with behave and dynamic environment:
        * Error in before_feature:
                before_scenario and after_scenario are not executed
                after_feature is executed
                each scenario is marked as failed
        * Error in before_scenario:
                after_scenario is executed
                the scenario is marked as failed
        * Error in after_scenario:
                the scenario status is not changed
        * Error in after_feature:
                the scenarios status are not changed
    """

    def __init__(self, **kwargs):
        """
        constructor
        :param kwargs: parameters set
        :param logger: logger instance
        :param show: determine if messages are displayed by console
        """
        logger_class = kwargs.get("logger", None)
        self.show = kwargs.get("show", True)
        self.logger = Logger(logger_class, self.show)
        self.init_actions()
        self.scenario_counter = 0
        self.feature_error = False
        self.scenario_error = False
        self.before_error_message = None

    def init_actions(self):
        """clear actions lists"""
        self.actions = {ACTIONS_BEFORE_FEATURE: [],
                        ACTIONS_BEFORE_SCENARIO: [],
                        ACTIONS_AFTER_SCENARIO: [],
                        ACTIONS_AFTER_FEATURE: []}

    def get_steps_from_feature_description(self, description):
        """
        get all steps defined in the feature description associated to each action
        :param description: feature description
        """
        self.init_actions()
        label_exists = EMPTY
        step_text_start = False
        for row in description:
            if label_exists != EMPTY:
                # The row is removed if it's a comment
                if row.strip().startswith("#"):
                    row = ""

                if any(row.startswith(x) for x in KEYWORDS):
                    self.actions[label_exists].append(row)
                elif row.strip()[-3:] in STEP_TEXT_SEPARATORS and step_text_start:
                    self.actions[label_exists][-1] = "%s\n      %s" % (self.actions[label_exists][-1], row)
                    step_text_start = False
                elif row.find(TABLE_SEPARATOR) >= 0 or step_text_start:
                    self.actions[label_exists][-1] = "%s\n      %s" % (self.actions[label_exists][-1], row)
                elif row.strip()[:3] in STEP_TEXT_SEPARATORS and not step_text_start:
                    self.actions[label_exists][-1] = "%s\n      %s" % (self.actions[label_exists][-1], row)
                    step_text_start = True
                else:
                    label_exists = EMPTY

            for action_label in self.actions:
                if row.lower().find(action_label) >= 0:
                    label_exists = action_label

    def __remove_prefix(self, step):
        """
        remove the step prefix to will be replaced by Given
        :param step: step text
        """
        step_length = len(step)
        for k in KEYWORDS:
            step = step.lstrip(k)
            if len(step) < step_length:
                break
        return step

    def __print_step_by_console(self, step):
        """
        print the step by console if the show variable is enabled
        :param step: step text
        """
        step_list = step.split('\n')
        for s in step_list:
            self.logger.by_console('    %s' % repr(s).replace("u'", "").replace("'", ""))

    def __execute_steps_by_action(self, context, action):
        """
        execute a steps set by action
        :param context: It’s a clever place where you and behave can store information to share around,
                        automatically managed by behave.
        :param action: action executed: see labels allowed above.
        """
        if len(self.actions[action]) > 0:
            if action == ACTIONS_BEFORE_SCENARIO:
                self.logger.by_console('\n')
                self.scenario_counter += 1
                self.logger.by_console(
                    "  ------------------ Scenario Nº: %d ------------------" % self.scenario_counter)
                self.logger.by_console('  %s:' % action)
            elif action in [ACTIONS_BEFORE_FEATURE, ACTIONS_AFTER_FEATURE]:
                self.logger.by_console('\n')

            for item in self.actions[action]:
                try:
                    self.__print_step_by_console(item)
                    self.logger.debug('Executing step defined in %s: %s' % (action, repr(item)))
                    context.execute_steps('''%s%s''' % (GIVEN_PREFIX, self.__remove_prefix(item)))
                except Exception as exc:
                    if action == ACTIONS_BEFORE_FEATURE:
                        self.feature_error = True
                        self.before_error_message = exc
                    elif action == ACTIONS_BEFORE_SCENARIO:
                        self.scenario_error = True
                        self.before_error_message = exc
                    self.logger.error(exc)
                    break

    def execute_before_feature_steps(self, context):
        """
        actions before the feature
        :param context: It’s a clever place where you and behave can store information to share around,
                        automatically managed by behave.
        """
        self.__execute_steps_by_action(context, ACTIONS_BEFORE_FEATURE)

        if self.feature_error:
            # Mark this Feature as skipped to do not execute any Scenario
            # Status will be changed to failed in after_feature method
            context.feature.mark_skipped()

    def execute_before_scenario_steps(self, context):
        """
        actions before each scenario
        :param context: It’s a clever place where you and behave can store information to share around,
                        automatically managed by behave.
        """
        self.__execute_steps_by_action(context, ACTIONS_BEFORE_SCENARIO)

        if self.scenario_error:
            # Mark this Scenario as skipped to do not execute any step
            # Status will be changed to failed in after_scenario method
            context.scenario.mark_skipped()

    def execute_after_scenario_steps(self, context):
        """
        actions after each scenario
        :param context: It’s a clever place where you and behave can store information to share around,
                        automatically managed by behave.
        """
        self.__execute_steps_by_action(context, ACTIONS_AFTER_SCENARIO)

        # Mark first step as failed when before_scenario has failed
        if self.scenario_error:
            error_message = self.before_error_message
            self.scenario_error = False
            self.before_error_message = None
            context.scenario.reset()
            self.fail_first_step_precondition_exception(context.scenario, error_message)
            raise Exception(f'Before scenario steps have failed: {error_message}')

    def execute_after_feature_steps(self, context):
        """
        actions after the feature
        :param context: It’s a clever place where you and behave can store information to share around,
                        automatically managed by behave.
        """
        self.__execute_steps_by_action(context, ACTIONS_AFTER_FEATURE)

        # Mark first step of each scenario as failed when before_feature has failed
        if self.feature_error:
            error_message = self.before_error_message
            self.feature_error = False
            self.before_error_message = None
            context.feature.reset()
            for scenario in context.feature.walk_scenarios():
                if scenario.should_run(context.config):
                    self.fail_first_step_precondition_exception(scenario, error_message)
                    if len(scenario.background_steps) > 0:
                        context.logger.warn('Background from scenario status udpated to fail')
            raise Exception(f'Before feature steps have failed: {error_message}')

    def fail_first_step_precondition_exception(self, scenario, error_message):
        """
        Fail first step in the given Scenario and add exception message for the output.
        This is needed because xUnit exporter in Behave fails if there are not failed steps.
        :param scenario: Behave's Scenario
        :param error_message: Exception message
        """
        # Behave is an optional dependency in toolium, so it is imported here
        from behave.model_core import Status
        if len(scenario.steps) > 0:
            scenario.steps[0].status = Status.failed
            scenario.steps[0].exception = Exception('Preconditions failed')
            scenario.steps[0].error_message = str(error_message)
        if len(scenario.background_steps) > 0:
            scenario.background_steps[0].status = Status.failed
            scenario.background_steps[0].exception = Exception('Preconditions failed')
            scenario.background_steps[0].error_message = str(error_message)
