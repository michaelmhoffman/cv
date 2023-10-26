#!/usr/bin/env python

"""panfilter.py: filter out parts of a pandoc document."""

from __future__ import absolute_import, division, print_function

__version__ = "0.1"

# Copyright 2015-2021, 2023 Michael M. Hoffman <michael.hoffman@utoronto.ca>

from argparse import Namespace
from contextlib import nullcontext
from datetime import date
from functools import partial
import json
from os import EX_OK
from pprint import pprint
import re
import sys
from typing import Any, Callable, Iterator, Optional, TextIO, TypedDict

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
PandocType = str
PandocContent = str | list | None
PrintCallable = Callable[..., None]

# documentation:
# Pandoc AST: https://hackage.haskell.org/package/pandoc-types/docs/Text-Pandoc-Definition.html
# lua filters: https://github.com/jgm/pandoc/blob/main/doc/lua-filters.md
# Python pandocfilters: https://github.com/jgm/pandocfilters

# XXX: some refactoring to do:
# type -> tag
# node -> element
# separate treatment of blocks vs. inlines if necessary
# that would involve turning PandocTree into BlockList

class PandocNode(TypedDict):
    t: PandocType
    c: PandocContent


PandocTree = list[PandocNode]


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
    cite_links = row.find("a", class_="gsc_a_ac")

    cites = next(iter(cite_links.contents), "0")

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


def unpack_node(node: PandocNode) -> tuple[PandocType, PandocContent]:
    node_type = node["t"]
    content = node.get("c")

    return node_type, content


def pack_node(node_type: PandocType,
              content: PandocContent) -> PandocNode:
    return {"t": node_type, "c": content}


def is_accepted_tree(tree: PandocTree,
                     section_year_min: Optional[int]) -> bool:
    # is section_year_min unset? -> True
    if section_year_min is None:
        return True

    # does any subnode have a max year <section_year_min? -> False
    for node in tree:
        node_type, content = unpack_node(node)

        if node_type == "Str":
            assert isinstance(content, str)

            node_years = [text_to_year(match.group(0))
                          for match in re_year.finditer(content)]
            if node_years and max(node_years) < section_year_min:
                return False

    # default -> True
    return True


def proc_bullet_str(node: PandocNode, citations: CitationsDict) -> None:
    node_type, content = unpack_node(node)

    if node_type == "Str":
        assert isinstance(content, str)

        if content.startswith("%CITES"):
            citation_id = content.partition(":")[2]
            node["c"] = "{:,}".format(int(citations[citation_id]))


def generate_bullet_tree(tree: PandocTree, citations: CitationsDict,
                         section_year_min: Optional[int]) \
                         -> Iterator[PandocNode]:
    if not is_accepted_tree(tree, section_year_min):
        return

    for node in tree:
        node_type, content = unpack_node(node)

        if node_type == "BulletList":
            assert isinstance(content, list)

            yield proc_bullet_list(node, citations, section_year_min)
        elif node_type == "Plain":
            assert isinstance(content, list)

            processed_content = list(generate_bullet_tree(content, citations,
                                                          section_year_min))
            yield pack_node(node_type, processed_content)
        elif isinstance(content, list):
            if not is_accepted_tree(content, section_year_min):
                continue

            yield node
        else:
            proc_bullet_str(node, citations)

            yield node


def generate_bullet_list(trees: list[PandocTree], citations: CitationsDict,
                         section_year_min: Optional[int]) \
                         -> Iterator[PandocTree]:
    for tree in trees:
        yield list(generate_bullet_tree(tree, citations, section_year_min))


def proc_bullet_list(node: PandocNode,
                     citations: CitationsDict,
                     section_year_min: Optional[int]) -> PandocNode:
    node_type, content = unpack_node(node)
    assert isinstance(content, list)

    processed_content = list(generate_bullet_list(content, citations,
                                                  section_year_min))

    return pack_node(node_type, processed_content)


def is_accepted_header(content: PandocContent,
                       section_exclude: frozenset[str]) -> bool:
    assert isinstance(content, list)

    subnode = content[0]
    subnode_type, subnode_content = unpack_node(subnode)

    # is paragraph explicitly excluded? -> False
    if subnode_type == "Str":
        assert isinstance(subnode_content, str)

        if subnode_content.partition(".")[0] in section_exclude:
            return False

    return True


def is_accepted_para(tree: PandocTree,
                     section_exclude: frozenset[str],
                     section_year_min: Optional[int]) -> bool:
    """Return whether paragraph should be accepted."""
    return (is_accepted_header(tree, section_exclude)
            and is_accepted_tree(tree, section_year_min))


def generate_tree(tree: PandocTree, config: ConfigDict,
                  include_ids: frozenset[str],
                  citations: CitationsDict,
                  log: PrintCallable) -> Iterator[PandocNode]:
    section_id = None
    section_accept = True
    section_exclude: frozenset[str] = frozenset()
    section_year_min = None

    for node in tree:
        node_type, content = unpack_node(node)

        if node_type == "Header":
            assert isinstance(content, list)

            section_id = content[1][0]
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
                    content[2] = [{"c": section_name, "t": "Str"}]

                section_exclude_list = section_config.get("exclude", [])
                assert isinstance(section_exclude_list, list)

                section_exclude = frozenset(section_exclude_list)
                log(" section_exclude:", *section_exclude)

                section_year_min = proc_section_year_min(section_config)

        if not section_accept:
            continue

        if node_type == "Para":
            assert isinstance(content, list)

            if not is_accepted_para(content, section_exclude,
                                    section_year_min):
                continue

            node["c"] = list(generate_bullet_tree(content, citations,
                                                  section_year_min))

        if node_type == "BulletList":
            node = proc_bullet_list(node, citations, section_year_min)

        pprint(node, sys.stderr)
        yield node


def get_log_func(verbose: bool) -> PrintCallable:
    if verbose:
        return info
    else:
        return noop


def proc_tree(tree: PandocTree, config: ConfigDict,
              include_ids: frozenset[str], citations: CitationsDict,
              verbose: bool) -> list:
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


def parse_args(args: list[str]) -> Namespace:
    from argparse import (ArgumentDefaultsHelpFormatter, ArgumentParser,
                          FileType)

    description = __doc__.splitlines()[0].partition(": ")[2]
    parser = ArgumentParser(description=description,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("infile", nargs="?", type=FileType(),
                        default=sys.stdin, metavar="FILE",
                        help="input file in Pandoc JSON format")
    parser.add_argument("--config", type=FileType(), default=nullcontext(),
                        metavar="FILE", help="file with YAML configuration")
    parser.add_argument("--verbose", action="store_true",
                        help="verbose output")

    version = "%(prog)s {}".format(__version__)
    parser.add_argument("--version", action="version", version=version)

    return parser.parse_args(args)


def main(argv: list[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)

    with args.infile as infile, args.config as config_file:
        panfilter(infile, config_file, args.verbose)

    return EX_OK


if __name__ == "__main__":
    sys.exit(main())
