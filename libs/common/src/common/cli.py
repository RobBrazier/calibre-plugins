from calibre.customize.ui import Source
from calibre.utils.config import OptionParser
import calibre.utils.logging as calibre_logging
from calibre.utils.logging import ThreadSafeLog
from calibre import setup_cli_handlers
import logging
import re
import threading
from queue import Queue


class MetadataCliHelper:
    def __init__(self, plugin: Source, name: str, identifier: str) -> None:
        self.name = name
        self.plugin = plugin
        self.identifier = identifier

    def option_parser(self):
        parser = OptionParser(usage=f"{self.name} [t:title] [a:authors] [i:id]")
        parser.add_option(
            "--verbose", "-v", default=False, action="store_true", dest="verbose"
        )
        parser.add_option(
            "--debug-api", default=False, action="store_true", dest="debug_api"
        )
        return parser

    def run(self, args):
        opts, args = self.option_parser().parse_args(args)
        if opts.debug_api:
            calibre_logging.default_log.filter_level = calibre_logging.DEBUG
        if opts.verbose:
            level = logging.DEBUG
            calibre_level = calibre_logging.DEBUG
        else:
            level = logging.INFO
            calibre_level = calibre_logging.INFO
        setup_cli_handlers(logging.getLogger(self.name), level)
        log = ThreadSafeLog(level=calibre_level)
        (title, authors, ids) = (None, [], {})
        for arg in args:
            if arg.startswith("t:"):
                title = arg.split(":", 1)[1]
            if arg.startswith("a:"):
                authors.append(arg.split(":", 1)[1])
                authors = [a.strip() for a in re.split(",|&", authors[0])]
            if arg.startswith("i:"):
                (idtype, identifier) = arg.split(":", 2)[1:]
                ids[idtype] = identifier

        result_queue = Queue()
        abort = threading.Event()
        self.plugin.identify(
            log, result_queue, abort, title=title, authors=authors, identifiers=ids
        )
        ranking = self.plugin.identify_results_keygen(title, authors, ids)
        for rank, result in enumerate(sorted(result_queue.queue, key=ranking), start=1):
            self._print_result(result, rank)

    def _print_result(self, result, ranking):
        if result.pubdate:
            pubdate = str(result.pubdate.date())
        else:
            pubdate = "Unknown"
        result_text = "(%d) - %s: %s [%s]" % (
            ranking,
            result.identifiers[self.identifier],
            result.title,
            pubdate,
        )
        print(result_text)
