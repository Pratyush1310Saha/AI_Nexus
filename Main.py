import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.layouts import TreeLayout, LayeredLayout
import random
from OpenAIHttpClient import OpenAIHttpClient
import json
import time
import requests

@st.cache_resource(show_spinner=False)
def getopenAiClient():
    return OpenAIHttpClient() 
client = getopenAiClient()

def generate_image_url(prompt: str):
    url = "https://datascienceopenaieastus-2.openai.azure.com/openai/deployments/Dalle3/images/generations?api-version=2024-02-01"
    try:
        response = requests.post(
            url = url,
            headers=client.headers,
            json = {
                "prompt": prompt,
                "n": 1,
                "size": '1024x1024'
            }
        ).json()
        image_url = response['data'][0]['url']
        return image_url
    except Exception as e:
        return "Sorry, I am unable to generate the image for you. Please try again later."
    
def get_employee_conversation_summary(name):
    conversation_summary = {}    
    employee_id = st.session_state['node_name_to_id'][name]
    if employee_id in st.session_state['conversation_summary']:
        conversation_summary[name] = f"Conversation summary with {name} till now: \n\n{st.session_state['conversation_summary'][employee_id]}"
    return json.dumps(conversation_summary)
    

def getChatMessages(chatHistory, curSystemMessage, curNodeName, parentName = "", parentSystemMessage = "", parentConversationSummary = ""):
    systemMessage = ""
    if parentName != "":
        systemMessage = f"\n\nHey {curNodeName}, you are currently assisting/reporting to {parentName} in their job"
        if parentSystemMessage != "":
            systemMessage += f", whose job description is -> \n\n{parentSystemMessage}"
        if parentConversationSummary != "":
            systemMessage += f"Till now the conversation summary with {parentName} is -> \n\n{parentConversationSummary}"
            
    if curSystemMessage != "":
        systemMessage += f"\n\nNow Your job description is -> \n\n{curSystemMessage}. You have to specifically focus on the tasks assigned to you related to your job description and provide the best possible assistance to the user."
        if parentName != "":
            systemMessage += " You may use the context information about your manager as well to provide better assistance to the user."
    
    if systemMessage == "":
        systemMessage = f"\n\nHey {curNodeName}, you are currently assisting the user. You have to specifically focus on the tasks assigned to you and provide the best possible assistance to the user."
    # print(systemMessage)
    chatMessages = [
        {
            'role': 'system',
            'content': systemMessage
        }
    ]
    startIndex = len(chatHistory) - 1
    userMessageCount = 0 
    while startIndex >= 0 and userMessageCount <= 10:
        if chatHistory[startIndex]['role'] == 'user':
            userMessageCount += 1
        startIndex -= 1
        
    for i in range(startIndex + 1, len(chatHistory)):
        message = chatHistory[i]
        chatMessages.append(
            message
        )
    return chatMessages
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
                if message["role"] == "tool" or (message["role"] == "assistant" and "tool_calls" in message):
                    continue
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # React to user input
        if query := input_display.chat_input("Hey there! How can I help you today?"):
            with chat_display:
                with st.chat_message("user"):
                    st.markdown(query)
            
                with st.chat_message("assistant"):
                    chatHistory = st.session_state[f"messages_{st.session_state['active_node']}"]
                    chatHistory.append({"role": "user", "content": query})
                    messagePlaceholder = st.empty()
                    fullResponse = ""
                    chatMessages = getChatMessages(chatHistory, employee_system_message, employee_label['content'], parent_name, parent_system_message, parent_conversation_summary)
                    with st.spinner("Fetching results..."):
                        response = client.getChatCompletionResponse(messages = chatMessages, employee_names = list(st.session_state['node_names'].values()))
                        print(response)
                    while response['choices'][0]['finish_reason'] == 'tool_calls':
                        st.session_state[f"messages_{st.session_state['active_node']}"].append({"role": "assistant", "content": response['choices'][0]['message']['content'], "tool_calls": response['choices'][0]['message']['tool_calls']})
                        for tool_call in response['choices'][0]['message']['tool_calls']:
                            function_name = tool_call['function']['name']
                            arguments = json.loads(tool_call['function']['arguments'])
                            
                            if function_name == 'generate_image':
                                function_response = generate_image_url(**arguments)
                            else:
                                function_response = get_employee_conversation_summary(**arguments)
                                
                            arguments['response'] = function_response
                            function_call_result_message = {
                                "role": "tool",
                                "content": json.dumps(arguments),
                                "tool_call_id": tool_call['id']
                            }                            
                            st.session_state[f"messages_{st.session_state['active_node']}"].append(function_call_result_message)
                        chatHistory = st.session_state[f"messages_{st.session_state['active_node']}"]
                        chatMessages = getChatMessages(chatHistory, employee_system_message, employee_label['content'], parent_name, parent_system_message, parent_conversation_summary)
                        response = client.getChatCompletionResponse(messages = chatMessages, employee_names = list(st.session_state['node_names'].values()))
                        
                    response = json.loads(response['choices'][0]['message']['content'])
                    curAnswer, curSummary = response['answer'], response['summary']
                    for i in range(0, len(curAnswer), 5):
                        fullResponse += curAnswer[i:i+5]
                        messagePlaceholder.markdown(fullResponse + "▌")
                        time.sleep(0.05)
                    messagePlaceholder.markdown(fullResponse)
                    st.session_state[f"messages_{st.session_state['active_node']}"].append({"role": "assistant", "content": curAnswer})
                    st.session_state['conversation_summary'][st.session_state['active_node']] = curSummary