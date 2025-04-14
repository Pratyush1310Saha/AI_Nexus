from enum import StrEnum

class FallbackMessages(StrEnum):
    TOOL_CALL_TIMEOUT_MESSAGE = "Unable to fetch the result from the tool within the time limit."
    RATE_LIMIT_ERROR_MESSAGE = "Rate limit exceeded."
    CONTENT_FILTER_ERROR_MESSAGE = "Request blocked due to content filter."
    GENERIC_ERROR_MESSAGE = "An unexpected error occured: {exception_string}"
    TOOL_FALLBACK_MESSAGE = "Sorry, I am unable to fetch the result at the moment."
    IMAGE_GENERATOR_TOOL_FALLBACK_MESSAGE = "Sorry, I am unable to generate the image at the moment."