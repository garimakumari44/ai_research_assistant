"""
Code aware chunking.
"""

from uuid import uuid4



class CodeChunker:


    def __init__(
        self,
        max_lines: int = 80,
    ):

        self.max_lines = max_lines



    def chunk(
        self,
        code: str,
        metadata: dict | None = None,
    ):


        lines = code.splitlines()


        chunks = []


        for i in range(
            0,
            len(lines),
            self.max_lines
        ):

            section = lines[
                i:i+self.max_lines
            ]


            text = "\n".join(
                section
            )


            chunks.append(
                {
                    "chunk_id": str(uuid4()),
                    "text": text,
                    "token_count": len(
                        text.split()
                    ),
                    "metadata": {
                        **(metadata or {}),
                        "type": "code",
                    },
                }
            )


        return chunks