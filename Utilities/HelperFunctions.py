from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from Core.AppPrompts import SystemMessageComponents
import json
from json_autocomplete import json_autocomplete

def getChatMessages(chatHistory, curSystemMessage, curNodeName, parentName = "", parentSystemMessage = "", parentConversationSummary = ""):
    systemMessage = ""
    if parentName != "":
        systemMessage = SystemMessageComponents.INTRODUCTION.value.format(curNodeName = curNodeName, parentName = parentName)
        if parentSystemMessage != "":
            systemMessage += SystemMessageComponents.PARENT_NODE_DESCRIPTION.value.format(parentName = parentName, parentDescription = parentSystemMessage)
        if parentConversationSummary != "":
            systemMessage += SystemMessageComponents.PARENT_NODE_CONVERSATION_SUMMARY.value.format(parentName = parentName, parentConversationSummary = parentConversationSummary)
            
    if curSystemMessage != "":
        systemMessage += SystemMessageComponents.CUR_NODE_DESCRIPTION.value.format(curSystemMessage = curSystemMessage)
        if parentName != "":
            systemMessage += SystemMessageComponents.CUR_NODE_PARENT_CONTEXT
    
    if systemMessage == "":
        systemMessage = SystemMessageComponents.DEFAULT_SYSTEM_MESSAGE.value.format(curNodeName = curNodeName)
    # Add the Instruction message to the system message
    systemMessage += SystemMessageComponents.INSTRUCTION.value
    chatMessages =[]
    for chat in chatHistory:
        if chat['role'] == 'user':
            chatMessages.append(HumanMessage(content = chat['content']))
        elif chat['role'] == 'assistant':
            chatMessages.append(AIMessage(content = chat['content']))
    chatMessages.append(SystemMessage(content = systemMessage)) # Add the system message at the end for better relevance to instructions
    return chatMessages

async def get_content_to_stream(previous_response, new_chunk):
    try:
        previous_response_json = json.loads(json_autocomplete(previous_response))
        current_response_json = json.loads(json_autocomplete(previous_response + new_chunk))

        previous_answer_string = previous_response_json.get("response", "") if previous_response_json else ""
        current_answer_string = current_response_json.get("response", "") if current_response_json else ""
        previous_answer_string = "" if previous_answer_string is None else previous_answer_string
        current_answer_string = "" if current_answer_string is None else current_answer_string
        
        delta = current_answer_string[len(previous_answer_string):]
        return delta
    except Exception as e:
        print(f"Error in get_content_to_stream: {e}")
        return ""