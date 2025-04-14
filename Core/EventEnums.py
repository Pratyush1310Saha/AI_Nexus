from enum import StrEnum

class EVENTSTREAMTYPE(StrEnum):
    TOOLSTART = "on_tool_start"
    TOOLEND = "on_tool_end"
    CUSTOMEVENT = "on_custom_event"
    CHATMODELSTART = "on_chat_model_start"
    CHATMODELSTREAM  = "on_chat_model_stream"
    CHATMODELEND = "on_chat_model_end"