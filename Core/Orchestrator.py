from enum import StrEnum
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from typing import List, Dict, Any
from openai import RateLimitError, BadRequestError

from Core.AppMessages import FallbackMessages

class NodeNames(StrEnum):
    AGENT_NODE = 'agent'
    FINAL_RESPOND_NODE = 'respond_to_user'
    TOOLS_NODE = 'tools'

class ConditionalEdgeReturnTypes(StrEnum):
    CONTINUE = 'continue'
    RESPOND_TO_USER = 'respond_to_user'
    HARD_STOP = 'hard_stop'

class AgentState(MessagesState):
    final_response: Any
    hard_stop: bool = False

class Orchestrator:
    def __init__(self, response_class):
        self.response_class = response_class
    
    def call_model(self, state:AgentState, model):
        try:
            response = model.invoke(state['messages'])
        except RateLimitError:
            response = AIMessage(content = FallbackMessages.RATE_LIMIT_ERROR_MESSAGE)
            state['hard_stop'] = True
        except BadRequestError as e:
            if 'content_filter' in str(e):
                response = AIMessage(content = FallbackMessages.CONTENT_FILTER_ERROR_MESSAGE)
            else:
                response = AIMessage(content = FallbackMessages.GENERIC_ERROR_MESSAGE.format(exception_string = str(e)))
            state['hard_stop'] = True
        except Exception as e:
            response = AIMessage(content = FallbackMessages.GENERIC_ERROR_MESSAGE.format(exception_string = str(e)))
            state['hard_stop'] = True
            
        if state.get('hard_stop', False):
            return {'messages': response, 'hard_stop': True}
        else:
            return {'messages': response, 'hard_stop': False}
        
    def respond_to_user(self, state: AgentState):
        if state.get('hard_stop', False):
            response = self.response_class(response = state['messages'][-1].content)
            return {'final_response': response}
        # Construct the final answer from the arguments of the last tool call
        response = self.response_class(**state['messages'][-1].tool_calls[0]['args'])
        return {'final_response': response}       
    
    def should_continue(self, state: AgentState) -> str:
        messages = state['messages']
        last_message = messages[-1]
        if state.get('hard_stop', False):
            return ConditionalEdgeReturnTypes.HARD_STOP
        # If there is only one tool call and it is the response tool call we respond to the user
        elif (
            len(last_message.tool_calls) == 1
            and last_message.tool_calls[0]['name'] == self.response_class.__name__
        ):
            return ConditionalEdgeReturnTypes.RESPOND_TO_USER
        # Otherwise we will use the tool node again
        else:
            return ConditionalEdgeReturnTypes.CONTINUE
        
    def get_graph(self, tools: List[Any], model: Any) -> StateGraph:
        # Create the state graph for the agent
        workflow = StateGraph(AgentState)
        tool_node = ToolNode(tools=tools, name=NodeNames.TOOLS_NODE)
        
        workflow.add_node(NodeNames.AGENT_NODE, lambda state: self.call_model(state, model))
        workflow.add_node(NodeNames.TOOLS_NODE, tool_node)
        workflow.add_node(NodeNames.FINAL_RESPOND_NODE, self.respond_to_user)
        
        workflow.set_entry_point(NodeNames.AGENT_NODE)
        
        workflow.add_conditional_edges(
            NodeNames.AGENT_NODE,
            self.should_continue,
            {
                ConditionalEdgeReturnTypes.CONTINUE: NodeNames.TOOLS_NODE,
                ConditionalEdgeReturnTypes.RESPOND_TO_USER: NodeNames.FINAL_RESPOND_NODE,
                ConditionalEdgeReturnTypes.HARD_STOP: NodeNames.FINAL_RESPOND_NODE,
            }
        )
        workflow.add_edge(NodeNames.TOOLS_NODE, NodeNames.AGENT_NODE)
        workflow.add_edge(NodeNames.FINAL_RESPOND_NODE, END)
        graph = workflow.compile()
        return graph