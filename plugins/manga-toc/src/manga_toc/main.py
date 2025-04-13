import os
from io import BytesIO

from calibre.customize import Plugin
from calibre.ebooks.oeb.polish.toc import get_toc, commit_toc
from calibre.gui2 import error_dialog, question_dialog
from calibre.gui2.toc.main import TOC
from calibre.gui2.tweak_book.plugin import Tool
from qt.core import QAction


class MangaTocTool(Tool):
    name = "manga-toc-tool"
    allowed_in_toolbar = True
    allowed_in_menu = True

    def __init__(self):
        self.plugin_path = os.path.dirname(os.path.abspath(__file__))

    def create_action(self, for_toolbar=True):
        action = QAction(get_icons("images/chapters.png"), _("Generate ToC"), self.gui)
        if not for_toolbar:
            self.register_shortcut(action, "manga-toc-tool")
        action.triggered.connect(self.generate_toc)
        return action

    def __enter__(self, *args):
        Plugin.__enter__(self, *args)

    def __exit__(self, *args):
        Plugin.__exit__(self, *args)

    def _get_client(self):
        from .config import prefs

        api_key = prefs["api_key"]
        if not api_key:
            raise Exception(
                "A Gemini API Key is required - please configure in settings"
            )
        from google import genai

        return genai.Client(api_key=api_key)

    @staticmethod
    def _normalise_path(base, path) -> str:
        base_dir = os.path.dirname(base)
        return os.path.normpath(os.path.join(base_dir, path))

    # -> (image url, links, contents toc index)
    def parse_links(self, toc, container) -> tuple[str, list[str], int]:
        contents_url: str | None = None
        contents_index: int | None = None
        for i, item in enumerate(toc):
            if not item.title:
                continue
            if item.title.lower() == "contents":
                contents_url = item.dest
                contents_index = i
                break
        if not contents_url:
            raise Exception("Unable to find contents entry")

        contents = container.parsed(contents_url)
        image = next(
            iter(
                [
                    self._normalise_path(contents_url, i.get("src"))
                    for i in contents.xpath("//*[local-name() = 'img']")
                ]
            ),
            None,
        )
        links = [
            self._normalise_path(contents_url, a.get("href"))
            for a in contents.xpath("//*[local-name() = 'a'][@href]")
        ]
        return image, links, contents_index

    def _get_image_contents(self, container, path):
        from PIL import Image

        data = container.raw_data(path, decode=False)
        image = Image.open(BytesIO(data))
        return image

    def _gemini_read_chapters(self, image) -> list[str]:
        client = self._get_client()
        result = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                image,
                "\n\n",
                "Please can you extract the chapter names from this attached image. Only return the chapter names, no page numbers or any other information that is present in the image. Just chapter names.\n",
                "Convert the text to Title Case and ensure that the chapters are numerically numbered (converting other schemes into numbers).\n",
                "e.g. CH102 -> Chapter 102, Chapter I -> Chapter 1, Chapter X -> Chapter 10.\n",
                "In the case of additional chapters e.g. 'Extra Story', 'Origial Story', 'Bonus' etc., leave those as-is, but still performing the Title Case transformations",
                "Do not format the response in any way, just do one chapter per line.",
            ],
        )
        return result.text.splitlines()

    def _confirm_apply(self, changes):
        mappings_string = "\n".join(changes)
        return question_dialog(
            self.gui,
            _("Add Generated Chapters?"),
            _(
                f"Chapter mappings have been successfully generated:\n\n{mappings_string}\n\nContinue with applying?"
            ),
        )

    def _update_toc(self, toc: TOC, contents_idx: int, entries: dict[str, str]):
        try:
            toc_entries: list[TOC] = []
            for dest, title in entries.items():
                toc_entries.append(TOC(title=title, dest=dest))
            if contents_idx > len(toc.children):
                toc.children.extend(toc_entries)
            else:
                toc.children[contents_idx:contents_idx] = toc_entries
            commit_toc(self.current_container, toc)
            # self.boss.show_current_diff()
            self.boss.apply_container_update_to_gui()
        except Exception:
            self.boss.revert_requested(self.boss.global_undo.previous_container)
            raise

    def generate_toc(self):
        with self:
            try:
                self.boss.add_savepoint("Before: Generate ToC")
                container = self.current_container
                toc = get_toc(container)
                image, links, contents_idx = self.parse_links(toc, container)
                contents_image = self._get_image_contents(container, image)
                chapters = self._gemini_read_chapters(contents_image)
                entries = {}
                if len(links) != len(chapters):
                    raise Exception(
                        f"Number of links [{len(links)}] ({links}) doesn't match Number of chapters [{len(chapters)}] ({chapters})"
                    )
                mappings = []
                for link, chapter in zip(links, chapters):
                    entries.update({link: chapter})
                    mappings.append(f"{chapter} => {link}")
                apply = self._confirm_apply(mappings)
                if apply:
                    self._update_toc(toc, contents_idx + 1, entries)
            except Exception:
                import traceback

                error_dialog(
                    self.gui,
                    _("Failed to generate chapters"),
                    _(
                        "Failed to generate chapters. click 'Show details' for more info"
                    ),
                    det_msg=traceback.format_exc(),
                    show=True,
                )
