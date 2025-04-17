import base64
from io import BytesIO

import openai
from PIL import Image
from pydantic import BaseModel

PROMPT = """
Look at the image and output the chapters that you see. Focus only on the text content visible in the image. Do not generate any content that isn't visible in the image.
Format the output in Title Case. Do not assume the ordering based on the first number that is read, only use numbering that is visible.

For numbered chapters (numbered being either numeric (e.g. 1,2,3) or roman numerals (e.g. I,II,X), format as 'Chapter [number]: [title]'. Ensure that all roman numerals are converted to their numerical equivalents.
For other chapters without numbers, format as '[category]: [title]' when a category is present. Omit the category when not.

Please can you match the chapter names against the <links> provided, using the page number next to the chapter as reference, omitting any that don't have a page.
IMPORTANT: Do not modify the input links to match chapter numbering on the contents page
"""


class Chapter(BaseModel):
    name: str
    link: str


class ChapterResponse(BaseModel):
    chapters: list[Chapter]


class LLMReader:
    def __init__(self, url: str, model: str, api_key: str) -> None:
        self.client = openai.OpenAI(api_key=api_key, base_url=url)
        self.model = model

    def read_chapters(self, links: list[str], image_bytes: bytes) -> dict[str, str]:
        image = Image.open(BytesIO(image_bytes))
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        image_url = f"data:{image.get_format_mimetype()};base64,{encoded_image}"
        links_text = "<links>\n" + "\n".join(links) + "\n</links>"

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": links_text},
                    ],
                },
            ],
            response_format=ChapterResponse,
        )
        content = response.choices[0].message.parsed
        print(content)
        return {chapter.link: chapter.name for chapter in content.chapters}
