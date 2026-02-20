"""
Copyright 2026 Telefónica Innovación Digital, S.L.
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

import logging

# AI library imports must be optional to allow installing Toolium without `ai` extra dependency
try:
    from langchain_core.messages import SystemMessage
    from langchain_core.tools import Tool
    from langchain_openai import AzureChatOpenAI, ChatOpenAI
    from langgraph.graph import END, START, MessagesState, StateGraph
    from langgraph.prebuilt import ToolNode, tools_condition

    AI_IMPORTS = True
except ImportError:
    AI_IMPORTS = False

from toolium.driver_wrappers_pool import DriverWrappersPool

logger = logging.getLogger(__name__)


def create_react_agent(system_message, tool_method, tool_description=None, provider=None, model_name=None, **kwargs):
    """
    Creates a ReAct agent using the provided system message, tool method and model name.

    :param system_message: The system message to set the behavior of the assistant
    :param tool_method: The method that the agent can use as a tool
    :param tool_description: Optional custom description for the tool. If not provided, uses the method's docstring
    :param provider: The AI provider to use (optional, 'azure' or 'openai')
    :param model_name: The name of the model to use (optional)
    :param kwargs: additional parameters to be passed to the LLM chat client
    :returns: A compiled ReAct agent graph
    """
    if not AI_IMPORTS:
        raise ImportError(
            "AI dependencies are not installed. Please run 'pip install toolium[ai]' to use langgraph features",
        )

    # Define LLM with bound tools
    llm = get_llm_chat(provider=provider, model_name=model_name, **kwargs)
    if tool_description:
        tools = [Tool(name=tool_method.__name__, description=tool_description, func=tool_method)]
    else:
        tools = [tool_method]
    llm_with_tools = llm.bind_tools(tools)

    # Define assistant with system message
    sys_msg = SystemMessage(content=system_message)

    def assistant(state: MessagesState):
        return {'messages': [llm_with_tools.invoke([sys_msg] + state['messages'])]}

    # Build graph
    builder = StateGraph(MessagesState)
    builder.add_node('assistant', assistant)
    builder.add_node('tools', ToolNode(tools))
    builder.add_edge(START, 'assistant')
    builder.add_conditional_edges(
        'assistant',
        tools_condition,
    )
    builder.add_edge('tools', 'assistant')
    builder.add_edge('assistant', END)

    # Compile graph
    logger.info('Creating ReAct agent with model %s and tools %s', model_name, tools)
    graph = builder.compile()
    return graph


def get_llm_chat(provider=None, model_name=None, **kwargs):
    """
    Get LLM Chat instance based on the provider and model name specified in the parameters or in the configuration file.

    :param provider: the AI provider to use (optional, 'azure' or 'openai')
    :param model_name: name of the model to use
    :param kwargs: additional parameters to be passed to the chat client
    :returns: langchain LLM Chat instance
    """
    config = DriverWrappersPool.get_default_wrapper().config
    provider = provider or config.get_optional('AI', 'provider', 'openai')
    model_name = model_name or config.get_optional('AI', 'openai_model', 'gpt-4o-mini')
    llm = AzureChatOpenAI(model=model_name, **kwargs) if provider == 'azure' else ChatOpenAI(model=model_name, **kwargs)
    return llm


def execute_agent(ai_agent, previous_messages=None):
    """
    Executes the given AI agent and logs all conversation messages and tool calls.

    :param ai_agent: The AI agent to be executed
    :param previous_messages: Optional list of previous messages with the tool to provide context to the agent
    :returns: The final state of the agent after execution
    """
    logger.info('Executing AI agent with previous messages: %s', previous_messages)
    initial_state = MessagesState(messages=previous_messages or [])
    final_state = ai_agent.invoke(initial_state)

    # Log all conversation messages and tool calls to help with debugging and understanding the agent's behavior
    logger.info('AI agent execution completed with %d messages', len(final_state['messages']))
    for msg in final_state['messages']:
        if msg.type == 'ai' and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                logger.debug(
                    '%s: calling to %s tool with args %s',
                    msg.type.upper(),
                    tool_call['name'],
                    tool_call['args'],
                )
        else:
            logger.debug('%s: %s', msg.type.upper(), msg.content)

    return final_state
