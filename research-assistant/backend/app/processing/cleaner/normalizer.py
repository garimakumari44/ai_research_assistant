import re
import unicodedata



class TextNormalizer:
    """
    Normalize extracted document text.
    Handles PDF artifacts, whitespace,
    unicode normalization.
    """

    def normalize_unicode(
        self,
        text: str
    ) -> str:

        return unicodedata.normalize(
            "NFKC",
            text
        )


    def remove_null_characters(
        self,
        text: str
    ) -> str:

        return text.replace(
            "\x00",
            ""
        )


    def normalize_whitespace(
        self,
        text: str
    ) -> str:

        # replace multiple spaces

        text = re.sub(
            r"[ \t]+",
            " ",
            text
        )


        # replace multiple new lines

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text
        )


        return text.strip()



    def normalize(
        self,
        text: str
    ) -> str:


        text = self.normalize_unicode(
            text
        )


        text = self.remove_null_characters(
            text
        )


        text = self.normalize_whitespace(
            text
        )


        return text