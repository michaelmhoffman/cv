#!/usr/bin/env python

"""panfilter.py: filter out parts of a pandoc document."""

from __future__ import absolute_import, division, print_function

__version__ = "0.1"

# Copyright 2015-2021, 2023 Michael M. Hoffman <michael.hoffman@utoronto.ca>

from datetime import date
from functools import partial
import json
import re
import sys
from typing import Any, Callable, Generator, Optional, TextIO, TypedDict

from bs4 import BeautifulSoup, Tag
import yaml

YEAR = date.today().year
SCHOLAR_FILENAME = "google-scholar.html"
HTML_PARSER = "lxml"

re_year = re.compile(r"19\d\d|20\d\d|present")

info = partial(print, file=sys.stderr)

CitationsDict = dict[str, str]
SectionConfigDict = dict[str, str | int | list[str]]
ConfigDict = dict[str, SectionConfigDict]
PandocNodeContent = str | list | None
PrintCallable = Callable[..., None]


class PandocNode(TypedDict):
    t: str
    c: PandocNodeContent


def text_to_year(text: str) -> int:
    if text == "present":
        return YEAR
    else:
        return int(text)


def proc_section_year_min(section_config: SectionConfigDict) -> Optional[int]:
    year_min = section_config.get("year-min")
    assert year_min is None or isinstance(year_min, int)

    if year_min is not None and year_min < 0:
        year_min += YEAR

    return year_min


def proc_scholar_row(row) -> tuple[str, str]:
    article_url = row.find("a", class_="gsc_a_at")["href"]
    article_id = article_url.rpartition(":")[2]
    cites = row.find("a", class_="gsc_a_ac").contents[0]

    return (article_id, cites)


def load_google_scholar(filename: str = SCHOLAR_FILENAME) -> CitationsDict:
    with open(filename, "rb") as infile:
        soup = BeautifulSoup(infile, HTML_PARSER)

    table = soup.find(id="gsc_a_t")

    assert isinstance(table, Tag)

    rows = table.find_all("tr", class_="gsc_a_tr")

    return dict(proc_scholar_row(row)
                for row in rows)


def read_config(config_file: Optional[TextIO]) -> \
        tuple[ConfigDict, frozenset[str]]:
    if config_file is None:
        config_raw = {}
    else:
        config_raw = yaml.safe_load(config_file)
        if config_raw is None:
            config_raw = {}

    config = dict((item["id"], dict(subitem for subitem in item.items()
                                    if subitem[0] != "id"))
                  for item in config_raw)

    include_ids = frozenset(section["id"] for section in config_raw)

    return config, include_ids


def text_accept(flag: bool) -> str:
    if flag:
        return "including"
    else:
        return "excluding"


def noop(*args: list[Any], **kwargs: dict[str, Any]) -> None:
    pass


def get_node_type_content(node: PandocNode) -> tuple[str, PandocNodeContent]:
    node_type = node["t"]
    node_content = node.get("c")

    return node_type, node_content


def proc_bullet_item(node: PandocNode, citations: CitationsDict) -> None:
    node_type, node_content = get_node_type_content(node)

    if node_type == "Str":
        assert isinstance(node_content, str)

        if node_content.startswith("%CITES"):
            citation_id = node_content.partition(":")[2]
            node["c"] = "{:,}".format(int(citations[citation_id]))


def proc_bullet(node_content: PandocNodeContent,
                citations: CitationsDict) -> None:
    # XXX: this will probably break, need to replace with something recursive
    assert isinstance(node_content, list)

    for subnode in node_content:
        for subsubnode in subnode:
            for subsubsubnode in subsubnode["c"]:
                proc_bullet_item(subsubsubnode, citations)


def is_accepted_para(node_content: PandocNodeContent,
                     section_exclude: frozenset[str],
                     section_year_min: Optional[int]) -> bool:
    """Return whether paragraph should be accepted."""
    assert isinstance(node_content, list)

    subnode = node_content[0]
    subnode_type, subnode_content = get_node_type_content(subnode)

    # is paragraph explicitly excluded? -> False
    if subnode_type == "Str":
        assert isinstance(subnode_content, str)

        if subnode_content.partition(".")[0] in section_exclude:
            return False

    # is section_year_min unset? -> True
    if section_year_min is None:
        return True

    # does any subnode have a max year <section_year_min? -> False
    for subnode in node_content:
        subnode_type, subnode_content = get_node_type_content(subnode)

        if subnode_type == "Str":
            assert isinstance(subnode_content, str)

            node_years = [text_to_year(match.group(0))
                          for match in re_year.finditer(subnode_content)]
            if node_years and max(node_years) < section_year_min:
                return False

    # default -> True
    return True


def generate_tree(tree: list, config: ConfigDict, include_ids: frozenset[str],
                  citations: CitationsDict, log: PrintCallable) \
                  -> Generator[PandocNode, None, None]:
    section_id = None
    section_accept = True
    section_exclude: frozenset[str] = frozenset()
    section_year_min = None

    for node in tree:
        node_type, node_content = get_node_type_content(node)

        if node_type == "Header":
            assert isinstance(node_content, list)

            section_id = node_content[1][0]
            section_accept = not include_ids or section_id in include_ids
            log(text_accept(section_accept), section_id)
            section_config = config.get(section_id)

            if section_config is None:
                # XXX: spaghetti
                section_exclude = frozenset()
                section_year_min = 0
            else:
                section_name = section_config.get("name")
                if section_name:
                    node_content[2] = [{"c": section_name, "t": "Str"}]

                section_exclude_list = section_config.get("exclude", [])
                assert isinstance(section_exclude_list, list)

                section_exclude = frozenset(section_exclude_list)
                log(" section_exclude:", *section_exclude)

                section_year_min = proc_section_year_min(section_config)

        if not section_accept:
            continue

        if node_type == "Para":
            if not is_accepted_para(node_content, section_exclude,
                                    section_year_min):
                continue

        if node_type == "BulletList":
            proc_bullet(node_content, citations)

        if node_type == "RawBlock":
            pass

        yield node


def get_log_func(verbose: bool) -> PrintCallable:
    if verbose:
        return info
    else:
        return noop


def proc_tree(tree: list, config: ConfigDict, include_ids: frozenset[str],
              citations: CitationsDict, verbose: bool) -> list:
    log = get_log_func(verbose)

    return list(generate_tree(tree, config, include_ids, citations, log))


def panfilter(infile: TextIO, config_file: Optional[TextIO] = None,
              verbose: bool = False) -> None:
    pandoc_in = json.load(infile)

    key = "blocks"
    tree = pandoc_in[key]

    citations = load_google_scholar()
    config, include_ids = read_config(config_file)

    pandoc_in[key] = proc_tree(tree, config, include_ids, citations,
                               verbose)
    json.dump(pandoc_in, sys.stdout)

    # XXX: print heading options
    # print(*(node["c"][1][0] for node in tree
    #         if node["t"] == "Header"), sep="\n")


def parse_args(args: list[str]):
    from argparse import (ArgumentDefaultsHelpFormatter, ArgumentParser,
                          FileType)

    description = __doc__.splitlines()[0].partition(": ")[2]
    parser = ArgumentParser(description=description,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("infile", nargs="?", type=FileType("r"),
                        default=sys.stdin, metavar="FILE",
                        help="input file in Pandoc JSON format")
    parser.add_argument("--config", type=FileType("r"),
                        metavar="FILE", help="file with YAML configuration")
    parser.add_argument("--verbose", action="store_true",
                        help="verbose output")

    version = "%(prog)s {}".format(__version__)
    parser.add_argument("--version", action="version", version=version)

    return parser.parse_args(args)


def main(argv: list[str] = sys.argv[1:]):
    args = parse_args(argv)

    return panfilter(args.infile, args.config, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
