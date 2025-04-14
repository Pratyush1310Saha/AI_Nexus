import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.layouts import TreeLayout
import random
import json
import asyncio
from langchain_core.messages import HumanMessage

from Utilities.AzureChatModel import AzureChatModel
from Utilities.HelperFunctions import getChatMessages, get_content_to_stream
from Tools.ContextRetrievalTool import ContextRetrievalTool, getContextRetrievalToolInput
from Tools.ImageGenerationTool import ImageGenerationTool
from Tools.FinalResponseTool import FinalResponse
from Core.EventEnums import EVENTSTREAMTYPE
from Core.AppMessages import FallbackMessages
from Core.Orchestrator import Orchestrator

# Configure page
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
    page_title="AI Nexus",
)

# Simple, clean CSS that works with Streamlit's layout system
st.markdown("""
<style>
    /* Remove default padding */
    .main .block-container {
        padding: 0 !important; 
        max-width: 100% !important;
    }

    /* Style sidebar */
    [data-testid="stSidebar"] {
        background-image: url('https://images.unsplash.com/photo-1671716784499-a3d26826d844?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8YWJzdHJhY3QlMjBiYWNrZ3JvdW5kfGVufDB8fDB8fHww');
        background-size: cover;
        background-repeat: no-repeat;
    }
    
    /* Style content columns to fill height */
    [data-testid="column"] {
        height: 100vh !important;
        padding: 0 !important;
    }

    /* Eliminate gap between columns */
    [data-testid="column-gap"] {
        width: 0 !important;
    }
    
    /* Make flow chart fill space */
    .stStreamlitFlow {
        height: 100% !important;
    }
    
    /* White overlay for sidebar text */
    .sidebar-content-box {
        background-color: rgba(255,255,255,0.7);
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
    }

    /* Hide status widget after completion */
    .hide-status [data-testid="stStatusWidget"] {
        display: none;
    }
    .chat-scroll-area {
        max-height: 60vh;
        overflow-y: auto;
        padding: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize model and tools
@st.cache_resource(show_spinner=False)
def getAzureChatModel():
    return AzureChatModel() 

model = getAzureChatModel()
tool_dict = {
    "ContextRetrievalTool": ContextRetrievalTool(),
    "ImageGenerationTool": ImageGenerationTool(),
    "FinalResponse": FinalResponse
}

# Streaming function for chat responses
async def process_stream(graph, inputs, chat_display, status_container):
    text_stream, full_response = "", ""
    response_started = False
    try:
        with chat_display.chat_message("assistant"):
            placeholder = st.empty()            
        async for event in graph.astream_events(input=inputs, version='v2'):
            event_type = event['event']
            if event_type == EVENTSTREAMTYPE.TOOLSTART:
                tool_obj = tool_dict.get(event['name'], None)
                if tool_obj and hasattr(tool_obj, 'status_message'):
                    status_container.update(label=tool_obj.status_message, state='running')
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

# Initialize session state
if 'nodes' not in st.session_state:
    st.session_state['nodes'] = []
    st.session_state['edges'] = []
    st.session_state['flow_key'] = f'flow_{random.randint(0, 1000)}'
    st.session_state['node_position'] = (100, 100)
    st.session_state['active_node'] = None
    st.session_state['node_names'] = {}
    st.session_state['node_name_to_id'] = {}
    st.session_state['system_messages'] = {}
    st.session_state['conversation_summary'] = {}
    st.session_state['parent_node'] = {}
    st.session_state['tools'] = tool_dict.copy()
    st.session_state['orchestrator'] = Orchestrator(response_class=FinalResponse)

# SIDEBAR SECTION
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

# MAIN CONTENT AREA - Two equal columns
col1, col2 = st.columns(2)

# FLOWCHART SECTION (LEFT COLUMN)
with col1:
    # Flowchart with full height
    result = streamlit_flow(st.session_state['flow_key'],
               st.session_state['nodes'],
               st.session_state['edges'],
               fit_view=True,
               allow_new_edges=True,
               layout=TreeLayout(direction='down'),
               get_edge_on_click=True,
               get_node_on_click=True,
               hide_watermark=True
            )
    
    # Handle flowchart interactions
    if result is not None:
        if "edge" in result:
            source_id = result.split('-')[1]
            target_id = result.split('-')[2]
            edge = StreamlitFlowEdge(id=result, source=source_id, target=target_id)
            st.session_state['edges'].append(edge)
            st.session_state['parent_node'][target_id] = source_id
        else:
            selected_employee_id = result
            if selected_employee_id != st.session_state['active_node']:
                st.session_state['active_node'] = selected_employee_id
st.sidebar.markdown('<h2 style="color: #006DC1; font-size: 20px;">To chat with an Employee -></h2>', unsafe_allow_html=True)
st.sidebar.subheader("Click on the employee you want to chat with on the flow board")
if st.session_state['active_node']:
    st.sidebar.subheader(f"Conversation summary with {st.session_state['node_names'][st.session_state['active_node']]} till now:")
    if st.session_state['active_node'] in st.session_state['conversation_summary']:
        st.sidebar.markdown(st.session_state['conversation_summary'][st.session_state['active_node']])
    else:
        st.sidebar.markdown("No conversation summary available.")
st.markdown(" ")
# CHAT SECTION (RIGHT COLUMN)
with col2:
    st.markdown('<div style="width:100%; height:100%;">', unsafe_allow_html=True)
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
        if query := input_display.chat_input("Hi! How can I help you today?"):
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
    st.markdown('</div>', unsafe_allow_html=True)