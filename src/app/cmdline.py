from __future__ import annotations

import argparse
import logging
import sys

from src.platform.filesystem import path_exists
from src.app import cmdline_keys as keys
from src.app.file_drop import handle_input_paths
from src.app.localization import ensure_selected_language_loaded
from src.app.localization_runtime import lang
from src.app.runtime.contexts.settings import resolve_settings
from src.app.runtime.contexts.ui import resolve_ui_host_window


def _console_print(*parts: object, **kwargs: object) -> None:
    """Write CLI output to the preserved console stream when available."""

    if hasattr(sys, "stdout_origin") and sys.stdout_origin is not None:
        stream = sys.stdout_origin
    elif sys.__stdout__ is not None:
        stream = sys.__stdout__
    else:
        stream = sys.stdout
    print(*parts, file=stream, **kwargs)


class CommandLineProcessor:
    """Command-line adapter extracted from bootstrap orchestration.

    Keeps CLI parsing isolated from startup window assembly so bootstrap can
    stay focused on runtime/UI orchestration.
    """

    def __init__(self, args_list):
        self.args_list = list(args_list)
        ensure_selected_language_loaded(*keys.ALL_KEYS)
        settings = resolve_settings()
        self.cmd_exit = settings.cmd_exit
        main_window = resolve_ui_host_window()
        if settings.cmd_invisible == "1":
            main_window.withdraw()
            main_window.iconify()
        self.parser = argparse.ArgumentParser(
            prog="tool",
            description=lang.resolve_required_ui_text(keys.PROGRAM_DESCRIPTION),
            exit_on_error=False,
        )
        subparser = self.parser.add_subparsers(
            title=lang.resolve_required_ui_text(keys.SUBCOMMANDS_TITLE),
            description=lang.resolve_required_ui_text(keys.SUBCOMMANDS_DESCRIPTION),
        )
        unpack_rom_parser = subparser.add_parser(
            "unpack",
            add_help=False,
            help=lang.resolve_required_ui_text(keys.UNPACK_COMMAND_HELP),
        )
        unpack_rom_parser.set_defaults(func=handle_input_paths)
        set_config_parse = subparser.add_parser(
            "set",
            help=lang.resolve_required_ui_text(keys.SET_COMMAND_HELP),
        )
        set_config_parse.set_defaults(func=self.set)
        get_config_parse = subparser.add_parser(
            "get",
            help=lang.resolve_required_ui_text(keys.GET_COMMAND_HELP),
        )
        get_config_parse.set_defaults(func=self.get)
        help_parser = subparser.add_parser(
            "help",
            help=lang.resolve_required_ui_text(keys.HELP_COMMAND_HELP),
        )
        help_parser.set_defaults(func=self.help)
        lpmake_parser = subparser.add_parser(
            "lpmake",
            help=lang.resolve_required_ui_text(keys.LPMAKE_COMMAND_HELP),
        )
        lpmake_parser.set_defaults(func=self.lpmake)
        if len(args_list) == 1 and args_list[0] not in ["help", "--help", "-h"]:
            result = handle_input_paths(args_list)
            for missing_path in result.missing_paths:
                logging.error(
                    lang.resolve_required_ui_text(keys.INPUT_PATH_MISSING_LOG_FORMAT),
                    missing_path,
                )
        if len(args_list) == 1 and args_list[0] in ["--help", "-h"]:
            self.help([])
        else:
            try:
                self._parse()
            except (argparse.ArgumentError, ValueError):
                logging.exception("CMD")
                self.help([])
                self.cmd_exit = "1"
        if self.cmd_exit == "1":
            sys.exit(1)

    def _parse(self) -> None:
        subcmd, subcmd_args = self.parser.parse_known_args(self.args_list)
        if not hasattr(subcmd, "func"):
            self.parser.print_help()
            return
        subcmd.func(subcmd_args)

    def set(self, args):
        if len(args) > 2:
            _console_print(
                lang.resolve_required_ui_text(keys.SET_TOO_MANY_ARGUMENTS_MESSAGE)
            )
            return
        name, value = args
        settings = resolve_settings()
        settings.set_value(name, value)
        logging.info(
            lang.resolve_required_ui_text(keys.SET_CONFIG_LOG_FORMAT),
            name,
            getattr(settings, name),
            value,
        )

    def get(self, args):
        if len(args) > 1:
            _console_print(
                lang.resolve_required_ui_text(keys.GET_TOO_MANY_ARGUMENTS_MESSAGE)
            )
            return
        (name,) = args
        _console_print(getattr(resolve_settings(), name))

    def help(self, args):
        if hasattr(sys, "stdout_origin"):
            self.parser.print_help(sys.stdout_origin)
        else:
            logging.warning(
                lang.resolve_required_ui_text(keys.STDOUT_ORIGIN_MISSING_LOG_MESSAGE)
            )

    def lpmake(self, arglist):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("outputdir", nargs="?", type=str, default=None)
        parser.add_argument(
            "workdir",
            type=str,
            help=lang.resolve_required_ui_text(keys.LPMAKE_WORK_DIRECTORY_HELP),
            action="store",
            default=None,
        )
        parser.add_argument(
            "--sparse",
            type=int,
            dest="Sparse:1.enable 0.disable",
            help=lang.resolve_required_ui_text(keys.LPMAKE_SPARSE_HELP),
            action="store",
            default=0,
        )
        parser.add_argument(
            "--group-name",
            type=str,
            action="store",
            help=lang.resolve_required_ui_text(keys.LPMAKE_GROUP_NAME_HELP),
            default="qti_dynamic_partitions",
        )
        parser.add_argument(
            "--size",
            type=int,
            help=lang.resolve_required_ui_text(keys.LPMAKE_SIZE_HELP),
            action="store",
            default=9126805504,
        )
        parser.add_argument(
            "--list",
            type=str,
            help=lang.resolve_required_ui_text(keys.LPMAKE_PARTITION_LIST_HELP),
            action="store",
            default=None,
        )
        parser.add_argument(
            "--delete",
            type=int,
            help=lang.resolve_required_ui_text(keys.LPMAKE_DELETE_SOURCE_HELP),
            action="store",
            default=0,
        )
        parser.add_argument(
            "--part_type",
            type=int,
            help=lang.resolve_required_ui_text(keys.LPMAKE_PARTITION_TYPE_HELP),
            action="store",
            default=1,
        )
        parser.add_argument(
            "--attrib",
            type=str,
            help=lang.resolve_required_ui_text(keys.LPMAKE_ATTRIBUTE_HELP),
            action="store",
            default="readonly",
        )
        args = parser.parse_args(arglist)
        if (
            not args.workdir
            or not args.outputdir
            or not path_exists(args.workdir)
            or not path_exists(args.outputdir)
        ):
            _console_print(
                lang.resolve_required_ui_text(keys.LPMAKE_PATH_MISSING_MESSAGE)
            )
            return


__all__ = ["CommandLineProcessor"]
