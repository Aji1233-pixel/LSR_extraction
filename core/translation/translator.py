import logging
from core.llm.freellm_client import FreeLLMClient

logger = logging.getLogger(__name__)

class TamilTranslator:
    def __init__(self, freellm_client: FreeLLMClient = None):
        # Re-use existing LLM client or initialize a new one
        self.client = freellm_client or FreeLLMClient()

    def translate(self, text: str) -> str:
        """
        Translates text to Tamil using the LLM client.
        Falls back to original text if translation fails.
        """
        if not text or not text.strip():
            return text

        prompt = (
            "You are an expert English to Tamil translator.\n"
            f"Translate the following text into clear Tamil: '{text}'\n"
            "Return ONLY the Tamil translation without any explanation, markdown, or extra quotes."
        )

        try:
            # Assuming freellm_client has a method like generate/chat/complete
            # Adjust the method call to match your FreeLLMClient interface
            translated_text = self.client.generate(prompt)
            if translated_text and translated_text.strip():
                return translated_text.strip()
            return text
        except Exception as e:
            logger.warning(f"LLM translation failed for '{text}': {e}")
            return text