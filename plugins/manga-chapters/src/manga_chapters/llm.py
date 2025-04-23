import base64
import mimetypes

import openai
from pydantic import BaseModel

BASE_PROMPT = """
Look at the image and output the chapters that you see. Focus only on the text content visible in the image. Do not generate any content that isn't visible in the image.
Format the output in Title Case. Do not assume the ordering based on the first number that is read, only use numbering that is visible.

For numbered chapters (numbered being either numeric (e.g. 1,2,3) or roman numerals (e.g. I,II,X), format as 'Chapter [number]: [title]'. Ensure that all roman numerals are converted to their numerical equivalents.
For other chapters without numbers, format as '[category]: [title]' when a category is present. Omit the category when not.
"""

LINKS_PROMPT = """
Match the chapter names against the <links> provided, using the page number next to the chapter as reference, omitting any that don't have a page.
IMPORTANT: Do not modify the input links to match chapter numbering on the contents page
"""

PAGES_PROMPT = """
Estimate the page urls, using the page number next to the chapter as a reference.
Use <contents-url> as an anchor - this is where the contents page is. The first chapter is usually the page after this.
The page urls to reference are in <pages> - Please match the chapter names against entries within this list.
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

    @staticmethod
    def get_image_url(image_filename: str, image_bytes: bytes) -> str:
        mime_type, _ = mimetypes.guess_type(image_filename)
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        image_url = f"data:{mime_type};base64,{encoded_image}"
        return image_url

    @staticmethod
    def format_response(response: ChapterResponse) -> dict[str, str]:
        return {chapter.link: chapter.name for chapter in response.chapters}

    def read_chapters_without_links(
        self,
        image_filename: str,
        image_bytes: bytes,
        contents_url: str,
        pages: list[str],
    ) -> dict[str, str]:
        pages_text = "<pages>\n" + "\n".join(pages) + "\n</pages>"
        image_url = self.get_image_url(image_filename, image_bytes)
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": BASE_PROMPT},
                        {"type": "text", "text": PAGES_PROMPT},
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {
                            "type": "text",
                            "text": f"<contents-url>{contents_url}</contents-url>",
                        },
                        {"type": "text", "text": pages_text},
                    ],
                },
            ],
            response_format=ChapterResponse,
        )
        content = response.choices[0].message.parsed
        return self.format_response(content)

    def read_chapters_with_links(
        self, links: list[str], image_filename: str, image_bytes: bytes
    ) -> dict[str, str]:
        links_text = "<links>\n" + "\n".join(links) + "\n</links>"

        image_url = self.get_image_url(image_filename, image_bytes)
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": BASE_PROMPT},
                        {"type": "text", "text": LINKS_PROMPT},
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": links_text},
                    ],
                },
            ],
            response_format=ChapterResponse,
        )
        content = response.choices[0].message.parsed
        return self.format_response(content)
