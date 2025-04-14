from enum import StrEnum

class SystemMessageComponents(StrEnum):
    INTRODUCTION = "Hey {curNodeName}, you are currently assisting/reporting to {parentName} in their job. "
    PARENT_NODE_DESCRIPTION = "{parentName} is a helpful assistant and is responsible for -> \n{parentDescription} "
    PARENT_NODE_CONVERSATION_SUMMARY = "Till now, {parentName} has had the following conversations with the user: \n{parentConversationSummary}\n\n"
    CUR_NODE_DESCRIPTION = "Now Your job description is -> \n{curSystemMessage}. You have to specifically focus on the tasks assigned to you related to your job description and provide the best possible assistance to the user. "
    CUR_NODE_PARENT_CONTEXT = "You may use the context information about your manager as well to provide better assistance to the user."
    DEFAULT_SYSTEM_MESSAGE = "Hey {curNodeName}, you are currently assisting the user. You have to specifically focus on the tasks assigned to you and provide the best possible assistance to the user."