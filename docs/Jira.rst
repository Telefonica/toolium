Jira Configuration
====================

First of all Jira must be enabled by setting the enabled property to true in config.cfg::

    [Jira]
    enabled: true

The rest of the properties can be configured as:

token: The OAuth token for the Jira account, can be created in Jira web page > Profile > Personal access tokens

Project data in order of preference:

- project_id: The project id, ,can be seen in Jira web page > Administration > Projects > The Edit html anchor href will have a pid= segment with the project id

- project_key: The shortened project upper case identifier that appears in the issues ids, see example below

- project_name: Full project name

- execution_url: The root server URL, see example below

Note: if the project cannot be located, available project for your user will be printed in toolium.log

onlyifchanges: true if previous state of the updated issues is similar true will force the update, false will omit it

summary_prefix: # TODO

fixversion: The fixversion field, see example below

labels: List of labels to be added

comments: A comment to be added in each of the test executions

build: Inactive field # TODO Pending field value confirmation

Full example::

    [Jira]
    enabled: true
    token: My OAuth token
    project_id: 12316620
    project_key: COMMONSRDF
    project_name: Apache Commons RDF
    execution_url: https://jira.atlassian.com
    onlyifchanges: true
    summary_prefix: [DEV][QA]
    fixversion: 4.12
    labels: [QA, label2, 3rdlabel]
    comments: "A new comment for the execution"

See `https://jira.readthedocs.io`_ for the complete Package documentation.

Jira API
====================

See request module for REST API calls `https://requests.readthedocs.io/en/latest/`_
And the json parsing module `https://docs.python.org/3/library/json.html`_
See `https://developer.atlassian.com/server/jira/platform/rest-apis/`_ for the the underlying API introduction.
And `https://docs.atlassian.com/software/jira/docs/api/REST/9.5.0/`_ for the underlying API full documentation.
