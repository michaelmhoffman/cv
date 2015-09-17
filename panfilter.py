#!/usr/bin/env python

"""panfilter.py: filter out parts of a pandoc document
"""

from __future__ import absolute_import, division, print_function
from future_builtins import ascii, filter, hex, map, oct, zip

__version__ = "0.1"

## Copyright 2015 Michael M. Hoffman <michael.hoffman@utoronto.ca>

from datetime import date
import json
from pprint import pprint
import re
import sys

from bs4 import BeautifulSoup
import yaml

YEAR = date.today().year
SCHOLAR_FILENAME = "google-scholar.html"
HTML_PARSER = "lxml"

re_year = re.compile(r"19\d\d|20\d\d|present")

def text_to_year(text):
    if text == "present":
        return YEAR
    else:
        return int(text)

def load_google_scholar(filename=SCHOLAR_FILENAME):
    with open(filename) as infile:
        soup = BeautifulSoup(infile, HTML_PARSER)

    table = soup.find(id="gsc_a_t")

    res = {}

    rows = table.find_all("tr", class_="gsc_a_tr")
    for row in rows:
        id = row.find("a", class_="gsc_a_at")["href"].rpartition(":")[2]
        cites = row.find("a", class_="gsc_a_ac").contents[0]
        res[id] = cites

    return res

def read_config(config_file):
    if config_file is None:
        config_raw = {}
    else:
        config_raw = yaml.load(config_file)
        if config_raw is None:
            config_raw = {}

    config = dict((item["id"], dict(subitem for subitem in item.items()
                                    if subitem[0] != "id"))
                  for item in config_raw)

    include_ids = frozenset(section["id"] for section in config_raw)

    return config, include_ids

def text_accept(flag):
    if flag:
        return "including"
    else:
        return "excluding"

def proc_tree(tree, config, include_ids, citations, verbose):
    section_id = None
    section_accept = True
    para_accept = True
    section_year_min = None
    res = []

    # XXX: this is pretty hairy, should probably have a generator that
    # eliminates this t/c stuff on the fly
    for node in tree:
        node_type = node["t"]
        node_content = node["c"]

        if node_type == "Header":
            section_id = node_content[1][0]
            section_accept = not include_ids or section_id in include_ids
            if verbose:
                print(text_accept(section_accept), section_id, file=sys.stderr)
            section_config = config.get(section_id)
            para_accept = True
            if section_config is not None:
                section_name = section_config.get("name")
                if section_name:
                    node_content[2] = [{"c": section_name, "t": "Str"}]

                section_exclude = frozenset(section_config.get("exclude", []))
                if verbose:
                    print(" section_exclude:", *section_exclude, file=sys.stderr)

                section_year_min = section_config.get("year-min")
                if section_year_min is not None and section_year_min < 0:
                    section_year_min = YEAR + section_year_min

        if not section_accept:
            continue

        if node_type == "Para":
            subnode = node_content[0]
            if (subnode["t"] == "Str"
                and subnode["c"].partition(".")[0] in section_exclude):
                para_accept = False
                if verbose:
                    print("", text_accept(para_accept), subnode["c"], file=sys.stderr)
                continue
            if verbose:
                    print("", text_accept(para_accept), subnode["c"], file=sys.stderr)

            for subnode in node_content:
                if subnode["t"] == "Str":
                    node_years = [text_to_year(match.group(0))
                                  for match in re_year.finditer(subnode["c"])]
                    if node_years and max(node_years) < section_year_min:
                        para_accept = False
                        break
            else:
                para_accept = True

        if not para_accept:
            continue

        # XXX: this will probably break, need to replace with something recursive
        if node_type == "BulletList":
            for subnode in node_content:
                for subsubnode in subnode:
                    for subsubsubnode in subsubnode["c"]:
                        subsubsubnode_content = subsubsubnode["c"]
                        if subsubsubnode["t"] == "Str" and subsubsubnode_content.startswith("%CITES"):
                            citation_id = subsubsubnode_content.partition(":")[2]
                            subsubsubnode["c"] = "{:,}".format(int(citations[citation_id]))

        res.append(node)

    return res

def panfilter(infile, config_file=None, verbose=False):
    pandoc_in = json.load(infile)
    metadata, tree = pandoc_in

    assert isinstance(metadata, dict)
    assert isinstance(tree, list)

    citations = load_google_scholar()
    config, include_ids = read_config(config_file)

    pandoc_out = metadata, proc_tree(tree, config, include_ids, citations, verbose)
    json.dump(pandoc_out, sys.stdout)

    # XXX: print heading options
    # print(*(node["c"][1][0] for node in tree
    #         if node["t"] == "Header"), sep="\n")

def parse_args(args):
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

def main(argv=sys.argv[1:]):
    args = parse_args(argv)

    return panfilter(args.infile, args.config, args.verbose)

if __name__ == "__main__":
    sys.exit(main())
