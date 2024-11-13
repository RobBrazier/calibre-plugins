# pyright: reportIncompatibleMethodOverride=false
from queue import Empty, Queue
from calibre.ebooks.metadata.sources.base import Option, Source
from .__version__ import __version_tuple__


class Hardcover(Source):
    name = "Hardcover"
    description = "Downloads metadata and covers from Hardcover.app"
    author = "Rob Brazier"
    version = __version_tuple__
    minimum_calibre_version = (7, 7, 0)

    ID_NAME = "hardcover"
    API_URL = "https://api.hardcover.app/v1/graphql"

    capabilities = frozenset(["identify", "cover"])
    touched_fields = frozenset(
        [
            "title",
            "authors",
            f"identifier:{ID_NAME}",
            f"identifier:{ID_NAME}-edition",
            "pubdate",
            "series",
            "tags",
        ]
    )
    options = (
        Option(
            name="api_key",
            type_="string",
            default="",
            label=_("API Key"),  # noqa: F821
            desc=_("Hardcover API Key"),  # noqa: F821
        ),
    )

    def __init__(self, *args, **kwargs):
        super(Source, self).__init__(*args, **kwargs)
        from .provider import HardcoverProvider

        self.provider = HardcoverProvider(self)

    def is_configured(self):
        return bool(self.prefs["api_key"])

    def cli_main(self, args):
        from common.cli import MetadataCliHelper

        MetadataCliHelper(self, self.name, self.ID_NAME).run(args)

    def get_cached_cover_url(self, identifiers):
        url = None
        hardcover_id = identifiers.get(self.ID_NAME, None)
        if hardcover_id is None:
            isbn = identifiers.get("isbn", None)
            if isbn is not None:
                hardcover_id = self.cached_isbn_to_identifier(isbn)
        if hardcover_id is not None:
            url = self.cached_identifier_to_cover_url(hardcover_id)
        return url

    def identify(
        self,
        log,
        result_queue,
        abort,
        title=None,
        authors=None,
        identifiers={},
        timeout=30,
    ):
        self.provider.identify(
            log, result_queue, abort, title, authors, identifiers, timeout
        )

    def download_cover(
        self,
        log,
        result_queue,
        abort,
        title=None,
        authors=None,
        identifiers={},
        timeout=30,
        get_best_cover=False,
    ):
        cached_url = self.get_cached_cover_url(identifiers)
        if cached_url is None:
            log.info("No cached cover found, running identify")
            rq = Queue()
            self.identify(
                log, rq, abort, title=title, authors=authors, identifiers=identifiers
            )
            if abort.is_set():
                return
            results = []
            while True:
                try:
                    results.append(rq.get_nowait())
                except Empty:
                    break
            results.sort(
                key=self.identify_results_keygen(
                    title=title, authors=authors, identifiers=identifiers
                )
            )
            for mi in results:
                cached_url = self.get_cached_cover_url(mi.identifiers)
                if cached_url is not None:
                    break
        if cached_url is None:
            log.info("No cover found")
            return

        if abort.is_set():
            return

        log("Downloading cover from: ", cached_url)
        try:
            cdata = self.browser.open_novisit(cached_url, timeout=timeout).read()
            result_queue.put((self, cdata))
        except Exception:
            log.exception("Failed to download cover from: ", cached_url)