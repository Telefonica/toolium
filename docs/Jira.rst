Jira Configuration
====================

First of all Jira must be enabled by setting the enabled property to true in config.cfg::

    [Jira]
    enabled: true

The rest of the properties can be configured as:

token: The OAuth token for the Jira account, can be created in Jira web page > Profile > Personal access tokens
project_id: The project id, ,can be seen in Jira web page > Administration > Projects > The Edit html anchor href will have a pid= segment with the project id
execution_url: The root server URL, see example below
onlyifchanges: true, if previous state of the updated issues is similar true will force the update, false will omit it
summary_prefix: # TODO
fixversion: The fixversion field, see example below
labels: # TODO
comments: # TODO
build: # TODO

Full example::

    [Jira]
    enabled: true
    token: My OAuth token
    project_id: 99999
    execution_url: https://jira.atlassian.com
    onlyifchanges: true
    summary_prefix: # TODO
    fixversion: 4.12
    labels: # TODO
    comments: # TODO
    build: # TODO

See `https://jira.readthedocs.io`_ for the complete Package documentation.

Jira API
====================

See request module for REST API calls `https://requests.readthedocs.io/en/latest/`_
And the json parsing module `https://docs.python.org/3/library/json.html`_
See `https://developer.atlassian.com/server/jira/platform/rest-apis/`_ for the the underlying API introduction.
And `https://docs.atlassian.com/software/jira/docs/api/REST/9.5.0/`_ for the underlying API full documentation.
