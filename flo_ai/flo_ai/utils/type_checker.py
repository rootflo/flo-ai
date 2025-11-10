from flo_ai.models import DocumentType, ImageType
from typing import Any

def is_document_message(message: Any) -> bool:
    """
    Check if the message is a document message.

    Args:
        message: The message to check.

    Returns:
        True if the message is a document message, False otherwise.
    """
    if message.content.document_type == DocumentType.PDF or message.content.document_type == DocumentType.TXT:
        return True
    return False

def is_image_message(message: Any) -> bool:
    """
    Check if the message is an image message.

    Args:
        message: The message to check.

    Returns:
        True if the message is an image message, False otherwise.
    """
    if message.content.image_type == ImageType.IMAGE_URL or message.content.image_type == ImageType.IMAGE_BYTES or message.content.image_type == ImageType.IMAGE_BASE64 or message.content.image_type == ImageType.IMAGE_FILE_PATH:
        return True
    return False