from .normalizer import TextNormalizer



class DocumentCleaner:
    """
    High level document cleaning pipeline.
    """


    def __init__(self):

        self.normalizer = TextNormalizer()



    def clean(
        self,
        text: str
    ) -> str:
        """
        Clean raw extracted text.
        """

        if not text:
            return ""


        cleaned_text = self.normalizer.normalize(
            text
        )


        return cleaned_text