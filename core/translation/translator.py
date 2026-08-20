from deep_translator import GoogleTranslator


class TamilTranslator:
    """
    Translates English text to Tamil.

    Original English text is never modified.
    """

    def __init__(self):
        self.translator = GoogleTranslator(
            source="en",
            target="ta"
        )

    def translate(self, text: str) -> str:
        """
        Translate English text to Tamil.

        Args:
            text: English text.

        Returns:
            Tamil translated text.
        """

        if not text or not text.strip():
            return text

        try:
            return self.translator.translate(text)

        except Exception as exc:
            raise RuntimeError(
                f"Translation failed: {exc}"
            ) from exc