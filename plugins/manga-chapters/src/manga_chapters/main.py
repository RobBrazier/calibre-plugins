import os

from calibre.customize import Plugin
from calibre.ebooks.oeb.polish.container import Container
from lxml.etree import _Element
from calibre.ebooks.oeb.polish.toc import get_toc, commit_toc
from calibre.gui2 import error_dialog, question_dialog
from calibre.gui2.toc.main import TOC
from calibre.gui2.tweak_book.plugin import Tool
from qt.core import QAction
from .config import prefs


class MangaTocTool(Tool):
    name = "manga-toc-tool"
    allowed_in_toolbar = True
    allowed_in_menu = True

    def __init__(self):
        self.plugin_path = os.path.dirname(os.path.abspath(__file__))
        self.prefs = prefs

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

    @staticmethod
    def _normalise_path(base, path) -> str:
        base_dir = os.path.dirname(base)
        return os.path.normpath(os.path.join(base_dir, path))

    @staticmethod
    def _find_image(contents: _Element) -> str | None:
        # Look for HTML img tags
        img_tags = contents.xpath("//*[local-name() = 'img']")
        if img_tags:
            # Check for src attribute
            src = img_tags[0].get("src")
            if src:
                return src

        # Look for SVG image tags
        image_tags = contents.xpath("//*[local-name() = 'image']")
        if image_tags:
            # SVG images can use href or xlink:href
            href = image_tags[0].get("href")
            if href:
                return href

            # Check for xlink:href which is common in SVG
            xlink_href = image_tags[0].get("{http://www.w3.org/1999/xlink}href")
            if xlink_href:
                return xlink_href

        return None

    # -> (image url, links, contents toc index, contents url)
    def parse_links(self, toc, container) -> tuple[str, list[str], int, str]:
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
            raise Exception(
                "Unable to find contents page. Please Update ToC to identify Contents page"
            )

        contents = container.parsed(contents_url)
        image = self._find_image(contents)
        if image:
            image = self._normalise_path(contents_url, image)
        links = [
            self._normalise_path(contents_url, a.get("href"))
            for a in contents.xpath("//*[local-name() = 'a'][@href]")
        ]
        return image, links, contents_index, contents_url

    def _get_image_contents(self, container, path) -> bytes:
        return container.raw_data(path, decode=False)

    def _read_chapters(
        self,
        links: list[str],
        image_filename: str,
        image: bytes,
        contents_url: str,
        pages: list[str],
    ) -> (dict[str, str], bool):
        from .llm import LLMReader

        url = self.prefs["llm_endpoint"]
        model = self.prefs["llm_model"]
        api_key = self.prefs["api_key"]
        reader = LLMReader(url, model, api_key)
        if len(links) > 0:
            return reader.read_chapters_with_links(links, image_filename, image), False
        return reader.read_chapters_without_links(
            image_filename, image, contents_url, pages
        ), True

    def _confirm_apply(self, changes: list[str], estimated: bool):
        mappings_string = "\n".join(changes)
        disclaimer = ""
        if estimated:
            disclaimer = "\nIMPORTANT: No links were found in the Contents page, so the Pages were estimated. Please validate these are correct."
        return question_dialog(
            self.gui,
            _("Add Generated Chapters?"),
            _(
                f"Chapter mappings have been successfully generated:\n\n{mappings_string}\n\nContinue with applying?{disclaimer}"
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

    def get_pages(self, container: Container) -> list[str]:
        return container.manifest_items_of_type("application/xhtml+xml")

    def generate_toc(self):
        with self:
            try:
                self.boss.add_savepoint("Before: Generate ToC")
                container = self.current_container
                toc = get_toc(container)
                image, links, contents_idx, contents_url = self.parse_links(
                    toc, container
                )
                pages = self.get_pages(container)
                contents_image = self._get_image_contents(container, image)
                chapters, estimated = self._read_chapters(
                    links, image, contents_image, contents_url, pages
                )
                mappings = []
                for link, chapter in chapters.items():
                    mappings.append(f"{chapter} => {link}")
                apply = self._confirm_apply(mappings, estimated)
                if apply:
                    self._update_toc(toc, contents_idx + 1, chapters)
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
