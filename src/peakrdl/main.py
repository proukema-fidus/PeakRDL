import argparse
import sys
from typing import TYPE_CHECKING, List, Dict

from systemrdl import RDLCompileError

from .__about__ import __version__
from .plugins.exporter import get_exporter_plugins
from .plugins.importer import get_importer_plugins
from .cmd.dump import Dump
from .cmd.list_globals import ListGlobals


if TYPE_CHECKING:
    from .subcommand import Subcommand


DESCRIPTION = """
PeakRDL is a control & status register model automation toolchain.

For help about a specific subcommand, try:
    peakrdl <command> --help

For more documentation, visit https://peakrdl.readthedocs.io

"""


class SubcommandHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def _format_action(self, action): # type: ignore
        parts = super(argparse.RawDescriptionHelpFormatter, self)._format_action(action)
        if action.nargs == argparse.PARSER:
            parts = "\n".join(parts.split("\n")[1:])
        return parts


class ReportPlugins(argparse.Action):
    def __call__ (self, parser, namespace, values, option_string = None): # type: ignore
        exporters = get_exporter_plugins()
        importers = get_importer_plugins()

        print("importers:")
        for importer in importers:
            print(f"\t'{importer.name}' --> {importer.dist_name} {importer.dist_version}")
        print("exporters:")
        for exporter in exporters:
            print(f"\t'{exporter.name}' --> {exporter.dist_name} {exporter.dist_version}")
        sys.exit(0)


def main() -> None:
    # Collect all subcommands
    subcommands = [
        Dump(),
        ListGlobals(),
    ] # type: List[Subcommand]
    subcommands += get_exporter_plugins()

    # Check for duplicates
    sc_dict = {} # type: Dict[str, Subcommand]
    for sc in subcommands:
        if sc.name in sc_dict:
            raise RuntimeError(f"More than one exporter plugin was registered with the same name '{sc.name}': \n\t{sc_dict[sc.name]}\n\t{sc}")
        sc_dict[sc.name] = sc

    # Initialize top-level arg parser
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=SubcommandHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--plugins", action=ReportPlugins, nargs=0,
        help="Report the PeakRDL plugins, their versions, then exit"
    )

    # Initialize subcommand arg parsers
    subgroup = parser.add_subparsers(
        title="subcommands",
        metavar="<subcommand>",
    )
    for subcommand in subcommands:
        subcommand._init_subparser(subgroup)

    # Execute!
    options = parser.parse_args()
    if not hasattr(options, 'subcommand'):
        parser.print_usage()
        print(f"{parser.prog}: error the following arguments are required: <subcommand>")
        sys.exit(1)
    try:
        options.subcommand.main(options)
    except RDLCompileError:
        sys.exit(1)
