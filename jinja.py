#!/usr/bin/env python
"""jinja: basic jinja templating
"""

from __future__ import absolute_import, division, print_function
from future_builtins import ascii, filter, hex, map, oct, zip  # noqa

__version__ = "$Revision: 871 $"

# Copyright 2011, 2015, 2016 Michael M. Hoffman <mmh1@uw.edu>

import codecs
import sys

from jinja2 import Environment, FileSystemLoader


def parse_variable_specs(specs):
    res = {}

    if not specs:
        return res

    for spec in specs:
        key, _, value = spec.partition("=")
        if not value:
            value = True

        res[key] = value

    return res


def jinja(infile, outfilename, variable_specs, search_dirnames):
    env = Environment(loader=FileSystemLoader(search_dirnames),
                      extensions=['jinja2.ext.do'])
    template = env.get_template(infile)

    variables = parse_variable_specs(variable_specs)

    with codecs.open(outfilename, "w", "utf-8") as outfile:
        print(template.render(variables), file=outfile)


def parse_args(args):
    from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

    description = __doc__.splitlines()[0].partition(": ")[2]
    parser = ArgumentParser(description=description,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("infile", metavar="INFILE",
                        help="input Jinja template")
    parser.add_argument("outfile", nargs="?", metavar="OUTFILE",
                        help="output file")

    parser.add_argument("-s", "--set", action="append", metavar="VAR=VALUE",
                        help="set variable VAR to VALUE")
    # to prepend, reverse after parsing
    parser.add_argument("--search-dir", action="append", default=["."],
                        help="prepend directory to template search path",)

    version = "%(prog)s {}".format(__version__)
    parser.add_argument("--version", action="version", version=version)

    return parser.parse_args(args)


def main(argv=sys.argv[1:]):
    args = parse_args(argv)

    search_dirnames = reversed(args.search_dir)
    return jinja(args.infile, args.outfile, args.set, search_dirnames)

if __name__ == "__main__":
    sys.exit(main())
