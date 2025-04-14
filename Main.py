import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.layouts import TreeLayout, LayeredLayout
import random
import json
import time
import asyncio
from langchain_core.messages import HumanMessage, AIMessage

from Utilities.AzureChatModel import AzureChatModel
from Utilities.HelperFunctions import getChatMessages, get_content_to_stream, process_stream
from Tools.ContextRetrievalTool import ContextRetrievalTool, getContextRetrievalToolInput
from Tools.ImageGenerationTool import ImageGenerationTool
from Tools.FinalResponseTool import FinalResponse
from Core.EventEnums import EVENTSTREAMTYPE
from Core.AppMessages import FallbackMessages
from Core.Orchestrator import Orchestrator

@st.cache_resource(show_spinner=False)
def getAzureChatModel():
    return AzureChatModel() 
model = getAzureChatModel()

tool_dict = {
    "ContextRetrievalTool": ContextRetrievalTool(),
    "ImageGenerationTool": ImageGenerationTool(),
    "FinalResponse": FinalResponse
}

async def process_stream(graph, inputs, chat_display, status_container):
    text_stream, full_response = "", ""
    response_started = False
    try:
        with chat_display.chat_message("assistant"):
            placeholder = st.empty()            
        async for event in graph.astream_events(input = inputs, version = 'v2'):
            event_type = event['event']
            if event_type == EVENTSTREAMTYPE.TOOLSTART:
                tool_obj = tool_dict[event['name']]
                if hasattr(tool_obj, 'status_message'):
                    payload = tool_obj.status_message
                    status_container.update(label=payload, state='running')
            if event_type == EVENTSTREAMTYPE.CHATMODELSTREAM:
                tool_calls = event['data']['chunk'].additional_kwargs.get('tool_calls', None)
                if tool_calls and tool_calls[0]['function']['name'] == FinalResponse.__name__:
                    response_started = True
                if tool_calls and response_started:
                    new_chunk = tool_calls[0]['function']['arguments']
                    content_to_stream = await get_content_to_stream(full_response, new_chunk)
                    full_response += new_chunk
                    if content_to_stream:
                        text_stream += content_to_stream
                        placeholder.markdown(text_stream)                    
        agent_response = event['data']['output']['final_response']
        return agent_response
    except Exception as e:
        with chat_display.chat_message("assistant"):
            st.error(f"Error: {str(e)}")
        status_container.update(label=FallbackMessages.GENERIC_ERROR_MESSAGE, state="error")

# Add custom CSS to the app
st.markdown(
    """
    <style>
    .st-emotion-cache-13ln4jf {
        width: 100%;
        padding: 6rem 1rem 10rem;
        max-width: 100vw;
        height: 100%;
    }
 
    .st-emotion-cache-0 {
    height: 100%;
    }
   
    .st-emotion-cache-1wmy9hl {
    height: 100%;
    }
 
    .st-emotion-cache-o7kj1z {
    height: 100%;
    }
 
    .st-emotion-cache-0 e1f1d6gn0 {
     height: 100%;  
    }
 
    .div_temp_class > div {
    height: 100%;
    }
    
    .st-emotion-cache-6qob1r{
        background-image: url('https://images.unsplash.com/photo-1671716784499-a3d26826d844?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8YWJzdHJhY3QlMjBiYWNrZ3JvdW5kfGVufDB8fDB8fHww');
        background-size: cover;  /* Cover the entire area */
        background-repeat: no-repeat;
    }
    
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize session state
if 'nodes' not in st.session_state:
    st.session_state['nodes'] = []
    st.session_state['edges'] = []
    st.session_state['flow_key'] = f'hackable_flow_{random.randint(0, 1000)}'
    st.session_state['node_position'] = (100, 100)  # Starting position for new nodes
    st.session_state['active_node'] = None  # Track the active node
    st.session_state['node_names'] = {}  # To map node IDs to names
    st.session_state['node_name_to_id'] = {}  # To map node names to IDs
    st.session_state['system_messages'] = {}
    st.session_state['conversation_summary'] = {}
    st.session_state['parent_node'] = {}
    st.session_state['tools'] = tool_dict.copy()
    st.session_state['orchestrator'] = Orchestrator(response_class = FinalResponse)
 
# Sidebar form to add a new employee
with st.sidebar:
    st.markdown('<label style="color: #4A5175; font-size: 48px; font-weight: bold;">AI Nexus</h1>', unsafe_allow_html=True)
    st.markdown('<h1 style="color: #006DC1; font-size: 20px; ">Add a New Employee</h1>', unsafe_allow_html=True)
   
    with st.form("new_employee_form"):
        employee_name = st.text_input("Enter Employee Name", value=f"Employee {len(st.session_state['nodes']) + 1}")
        invisible_char = "\u200B"*len(st.session_state['nodes'])
        employee_system_message = st.text_input("Describe employee's job description", placeholder = f"Type Here {invisible_char}")
        submit = st.form_submit_button("Create Employee")
 
    if submit:
        # Increment position for new nodes
        x, y = st.session_state['node_position']
        new_x = x + 100  # Increment X position by 100 pixels
        new_y = y + 100  # Increment Y position by 100 pixels
        st.session_state['node_position'] = (new_x, new_y)
 
        employee_id = str(len(st.session_state['nodes']) + 1)
 
        # Create the new employee node with the employee name
        new_employee = StreamlitFlowNode(
            id=employee_id,
            pos=(new_x, new_y),
            data={'label': employee_name},  # Ensure 'label' is set correctly
            connectable=True,
            draggable=True,
            background='https://images.pexels.com/photos/28295149/pexels-photo-28295149/free-photo-of-fotografia-de-bodas.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2'
        )
        # Add the new employee to the session state
        st.session_state['nodes'].append(new_employee)
        st.session_state['node_names'][employee_id] = employee_name  # Map employee ID to name
        st.session_state['node_name_to_id'][employee_name] = employee_id  # Map employee name to ID
        st.session_state['system_messages'][employee_id] = employee_system_message
 
        # Rerun the app to display the new employee
        st.session_state['flow_key'] = f'hackable_flow_{random.randint(0, 1000)}'
        st.rerun()
 
# Create columns for layout
col1, col2 = st.columns([7, 3])  # 70% and 30% width
with col1.container():
    selected_employee_id = None
    # Flowchart Generator
    result = streamlit_flow(st.session_state['flow_key'],
                   st.session_state['nodes'],
                   st.session_state['edges'],
                   fit_view=True,
                   allow_new_edges=True,
                   layout = TreeLayout(direction = 'down'),
                   get_edge_on_click= True,
                   get_node_on_click= True,
                   hide_watermark= True
                )
    if result is not None:
        if "edge" in result:
            source_id = result.split('-')[1]
            target_id = result.split('-')[2]
            edge = StreamlitFlowEdge(id = result, source=source_id, target=target_id)
            st.session_state['edges'].append(edge)
            st.session_state['parent_node'][target_id] = source_id
        else:
            selected_employee_id = result
    st.session_state['active_node'] = selected_employee_id
# Employee selection and chat

st.sidebar.markdown('<h2 style="color: #006DC1; font-size: 20px;">To chat with an Employee -></h2>', unsafe_allow_html=True)
st.sidebar.subheader("Click on the employee you want to chat with on the flow board")
if st.session_state['active_node']:
    st.sidebar.subheader(f"Conversation summary with {st.session_state['node_names'][st.session_state['active_node']]} till now:")
    if st.session_state['active_node'] in st.session_state['conversation_summary']:
        st.sidebar.markdown(st.session_state['conversation_summary'][st.session_state['active_node']])
    else:
        st.sidebar.markdown("No conversation summary available.")
st.markdown(" ")

with col2:
    header_display = st.container(height = 250, border = False)
    chat_display = st.container(height = 850, border = False)
    input_display = st.container(height = 100, border = False)
    
    if st.session_state['active_node']:
        # Get the selected employee node
        selected_employee = next(
            (employee for employee in st.session_state['nodes'] if employee.id == st.session_state['active_node']),
            None
        )

        if selected_employee:
            # Check if 'label' key exists and retrieve it
            employee_label = selected_employee.data.get('label', selected_employee.data)
            #print(employee_label['content'])
        else:
            employee_label = 'Unknown Employee'
        # st.write(f"Employee Label: {employee_label}")
        with header_display:
            st.title(f"Chat with {employee_label['content']}")  # Display employee name
            if st.session_state['active_node'] in st.session_state['system_messages']:
                employye_info = f"Job description: {st.session_state['system_messages'][st.session_state['active_node']]}"
                st.subheader(employye_info)

        # Get selected employee system message along with parent node's system message and conversation summary
        employee_system_message = st.session_state['system_messages'][st.session_state['active_node']]
        parent_node_id = st.session_state['parent_node'].get(st.session_state['active_node'], None)
        parent_name = st.session_state['node_names'].get(parent_node_id, "")
        parent_system_message = st.session_state['system_messages'].get(parent_node_id, "")
        parent_conversation_summary = st.session_state['conversation_summary'].get(parent_node_id, "")
        # Initialize chat history for the selected employee
        if f"messages_{st.session_state['active_node']}" not in st.session_state:
            st.session_state[f"messages_{st.session_state['active_node']}"] = []

        # Display chat messages from history on app rerun
        for message in st.session_state[f"messages_{st.session_state['active_node']}"]:
            with chat_display:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    
        st.session_state['tools']['ContextRetrievalTool'].session_state = st.session_state
        st.session_state['tools']['ContextRetrievalTool'].args_schema = getContextRetrievalToolInput(list(st.session_state['node_names'].values()))
        tools = list(st.session_state['tools'].values())
        agent = model.bind_tools(tools, tool_choice = 'any')
        graph = st.session_state['orchestrator'].get_graph(tools, agent)
        chatHistory = st.session_state[f"messages_{st.session_state['active_node']}"]
        previous_conversation = getChatMessages(chatHistory, employee_system_message, employee_label['content'], parent_name, parent_system_message, parent_conversation_summary)

        # React to user input
        if query := input_display.chat_input("Hey there! How can I help you today?"):
            st.session_state[f"messages_{st.session_state['active_node']}"].append({"role": "user", "content": query})
            previous_conversation.append(HumanMessage(content = query))
            with chat_display.chat_message("user"):
                st.markdown(query)
            
            with chat_display.chat_message("assistant"):
                status_container = st.status("Fetching response...")
                placeholder = st.empty()
                
            text_stream = ""
            inputs = {'messages': previous_conversation}
            agent_response = asyncio.run(process_stream(graph, inputs, chat_display, status_container))
            if agent_response:
                # Append the assistant's response to the chat history
                st.session_state[f"messages_{st.session_state['active_node']}"].append({"role": "assistant", "content": agent_response.response})
                # Append the conversation summary to the chat history
                st.session_state['conversation_summary'][st.session_state['active_node']] = agent_response.summary
                status_container.update(label='Done!', state='complete', expanded=False)
                # remove the status_container now since the answer is already displayed
                status_container.empty()