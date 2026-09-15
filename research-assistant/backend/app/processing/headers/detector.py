import re
from typing import List, Dict


class HeaderDetector:
    """
    Detect document headers and section structure.
    
    Supports:
    - Markdown headers
    - Numbered sections
    """


    MARKDOWN_PATTERN = re.compile(
        r"^(#{1,6})\s+(.*)$"
    )


    NUMBERED_PATTERN = re.compile(
        r"^(\d+(\.\d+)*)\s+(.*)$"
    )


    def detect(
        self,
        text: str
    ) -> List[Dict]:
        """
        Extract headers from document text.

        Returns:
        [
            {
                "title": "Introduction",
                "level": 1,
                "line": 0
            }
        ]
        """

        headers = []


        lines = text.split("\n")


        for index, line in enumerate(lines):

            line = line.strip()


            if not line:
                continue



            # Markdown headers

            markdown_match = self.MARKDOWN_PATTERN.match(
                line
            )


            if markdown_match:

                hashes, title = markdown_match.groups()


                headers.append(
                    {
                        "title": title.strip(),

                        "level": len(hashes),

                        "line": index
                    }
                )


                continue



            # Numbered headers

            numbered_match = self.NUMBERED_PATTERN.match(
                line
            )


            if numbered_match:

                number, _, title = numbered_match.groups()


                level = number.count(".") + 1


                headers.append(
                    {
                        "title": title.strip(),

                        "level": level,

                        "number": number,

                        "line": index
                    }
                )


        return headers