import os
import tempfile
import asyncio
import aiofiles
from typing import Optional

from openai import AzureOpenAI

from ai_companion.core.exceptions import SpeechToTextError
from ai_companion.settings import settings


class SpeechToText:
    """A class to handle speech-to-text conversion using Azure OpenAI's Whisper model."""

    def __init__(self):
        """Initialize the SpeechToText class and validate environment variables."""
        self._validate_env_vars()
        self._client: Optional[AzureOpenAI] = None

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        try:
            if not settings.AZURE_OPENAI_API_KEY:
                raise ValueError("Missing required setting: AZURE_OPENAI_API_KEY")
            # Check for Whisper model name
            if not hasattr(settings, 'STT_MODEL_NAME'):
                raise ValueError("Missing required setting: STT_MODEL_NAME")
        except AttributeError:
            raise ValueError("Missing required setting: AZURE_OPENAI_API_KEY")

    @property
    def client(self) -> AzureOpenAI:
        """Get or create Azure OpenAI client instance using singleton pattern."""
        if self._client is None:
            self._client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
        return self._client

    async def transcribe(self, audio_data: bytes) -> str:
        """Convert speech to text using Azure OpenAI's Whisper model.

        Args:
            audio_data: Binary audio data

        Returns:
            str: Transcribed text

        Raises:
            ValueError: If the audio file is empty or invalid
            RuntimeError: If the transcription fails
        """
        if not audio_data:
            raise ValueError("Audio data cannot be empty")

        try:
            # Create a temporary file with .wav extension
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            try:
                # Use aiofiles to read the file asynchronously
                async with aiofiles.open(temp_file_path, "rb") as audio_file:
                    file_content = await audio_file.read()
                
                # Use the STT model name from settings
                transcription = self.client.audio.transcriptions.create(
                    file=file_content,
                    model=settings.STT_MODEL_NAME,
                    language="en",
                    response_format="text",
                )

                if not transcription:
                    raise SpeechToTextError("Transcription result is empty")

                return transcription

            finally:
                # Clean up the temporary file using asyncio.to_thread
                await asyncio.to_thread(os.unlink, temp_file_path)

        except Exception as e:
            raise SpeechToTextError(
                f"Speech-to-text conversion failed: {str(e)}"
            ) from e
