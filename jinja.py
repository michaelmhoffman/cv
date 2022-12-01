#!/usr/bin/env python
"""jinja: basic jinja templating
"""

__version__ = "$Revision: 871 $"

# Copyright 2011, 2015, 2016, 2019, 2020, 2022 Michael M. Hoffman <mmh1@uw.edu>

from argparse import Namespace
from calendar import month_abbr, month_name
import codecs
from contextlib import AbstractContextManager, nullcontext
from os import EX_OK
import sys
from typing import Mapping, Optional, Sequence, Union

from jinja2 import Environment, FileSystemLoader, Template
from jinja2.meta import find_referenced_templates


MONTH_ABBRS = dict(zip(month_name[1:], month_abbr[1:]))
ENCODING = "utf-8"


def parse_variable_spec(spec: str) -> tuple[str, Union[str, bool]]:
    match spec.partition("="):
        case key, _, value if value:
            return key, value
        case key, _, _:
            # value is empty -> consider it to be a boolean that is true
            return key, True

    # can't happen, this silences mypy complaints
    assert False


def parse_variable_specs(specs: Sequence[str]) -> Mapping[str, Union[str, bool]]:
    return dict(parse_variable_spec(spec)
                for spec in specs)


def replace_dates(text: str) -> str:
    for name, abbr in MONTH_ABBRS.items():
        text = text.replace(name, abbr)

    return text


def open_outfile(filename: Optional[str]) -> AbstractContextManager:
    """Return context manager for outfile.

    None -> sys.stdout"""
    if filename is None:
        return nullcontext(codecs.getwriter(ENCODING)(sys.stdout.buffer))
    else:
        return codecs.open(filename, "w", ENCODING)


def get_dependencies(infile: str, env: Environment) -> str:
    assert isinstance(env.loader, FileSystemLoader)

    source, filename, _ = env.loader.get_source(env, infile)
    template = env.parse(source, None, filename)

    return " ".join(referenced_template
                    for referenced_template in find_referenced_templates(template)
                    if referenced_template is not None)


def render(infile: str, env: Environment, variable_specs: Sequence[str], abbr_months: Optional[bool]) -> str:
    template = env.get_template(infile)

    variables = parse_variable_specs(variable_specs)

    res = template.render(variables)
    if abbr_months:
        res = replace_dates(res)

    return res


def jinja(infilename: str, outfilename: Optional[str], variable_specs: Sequence[str],
          search_dirnames: Sequence[str], abbr_months: Optional[bool],
          print_dependencies: Optional[bool]) -> int:
    env = Environment(loader=FileSystemLoader(search_dirnames),
                      extensions=['jinja2.ext.do'])

    if print_dependencies:
        text = get_dependencies(infilename, env)
    else:
        text = render(infilename, env, variable_specs, abbr_months)

    with open_outfile(outfilename) as outfile:
        print(text, file=outfile)

    return EX_OK


def parse_args(argv: list[str]) -> Namespace:
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

    parser.add_argument("--abbr-months", action="store_true",
                        help="abbreviate months")

    parser.add_argument("--print-dependencies", action="store_true",
                        help="output dependencies instead of rendering template")

    version = "%(prog)s {}".format(__version__)
    parser.add_argument("--version", action="version", version=version)

    return parser.parse_args(argv)


def main(argv: list[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)

    search_dirnames = list(reversed(args.search_dir))
    return jinja(args.infile, args.outfile, args.set, search_dirnames,
                 args.abbr_months, args.print_dependencies)


if __name__ == "__main__":
    sys.exit(main())
