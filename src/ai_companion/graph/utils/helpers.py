import re

from langchain_core.output_parsers import StrOutputParser
from langchain_openai import AzureChatOpenAI

from ai_companion.modules.speech import TextToSpeech
from ai_companion.settings import settings
from ai_companion.modules.image.text_to_image import TextToImage
from ai_companion.modules.image.image_to_text import ImageToText


def get_chat_model(temperature: float = 0.7):
    return AzureChatOpenAI(
        deployment_name=settings.AZURE_OPENAI_DEPLOYMENT,
        openai_api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        temperature=temperature,
    )


def get_text_to_speech_module():
    return TextToSpeech()


def get_text_to_image_module():
    return TextToImage()


def get_image_to_text_module():
    return ImageToText()


def remove_asterisk_content(text: str) -> str:
    """Remove content between asterisks from the text."""
    return re.sub(r"\*.*?\*", "", text).strip()


class AsteriskRemovalParser(StrOutputParser):
    def parse(self, text):
        return remove_asterisk_content(super().parse(text))
