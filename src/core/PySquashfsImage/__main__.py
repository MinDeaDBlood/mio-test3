#!/usr/bin/env python

import argparse
import os
import posixpath
import sys

from datetime import datetime, timedelta
from time import localtime

from src.core.diagnostics import emit

from . import SquashFsImage, __version__
from .const import Compression
from .extract import extract_dir, extract_file
from .file import BlockDevice, CharacterDevice
from .util import find_superblocks

try:
    from datetime import timezone
except ImportError:
    pass

_is36 = sys.version_info >= (3, 6)
if not _is36:
    from dateutil.tz import tzlocal, tzutc

    UTC = tzutc()
else:
    UTC = timezone.utc

DTFMT = "%Y-%m-%d %H:%M:%S"
ROOT = posixpath.sep


def extract(args):
    with SquashFsImage.from_file(args.file, args.offset) as image:
        file = image.select(args.path)
        if file is None:
            raise Exception("{} not found".format(args.path))
        parent = args.dest or ""
        basename = os.path.basename(file.path) or "squashfs-root"
        dest = os.path.join(parent, basename)
        dirname = os.path.dirname(dest)
        if dirname and not os.path.isdir(dirname):
            os.makedirs(dirname)
        if file.is_dir:
            extract_dir(file, dest, args.force, quiet=args.quiet)
        else:
            extract_file(file, dest, args.force, quiet=args.quiet)


def _dtfromts(timestamp, utc=False):
    if utc:
        tz = UTC
    elif _is36:
        time = localtime(timestamp)
        tz = timezone(timedelta(seconds=time.tm_gmtoff), time.tm_zone)
    else:
        tz = tzlocal()
    return datetime.fromtimestamp(timestamp, tz)


def print_file(file, utc=False, show_tz=False):
    width = 25 - len(str(file.uid)) - len(str(file.gid))
    if isinstance(file, (BlockDevice, CharacterDevice)):
        width = max(0, width - 7)
        data = "{:{width}}{:3d},{:3d}".format(" ", file.major, file.minor, width=width)
    else:
        width = max(0, width)
        data = "{:{width}}".format(file.inode.data, width=width)
    dt = _dtfromts(file.inode.time, utc)
    emit(
        "{} {}/{} {} {} {}".format(
            file.filemode,
            file.uid,
            file.gid,
            data,
            dt if show_tz else dt.strftime(DTFMT),
            file.path,
        )
        + (" -> {}".format(file.readlink()) if file.is_symlink else "")
    )


def list_(args):
    types = args.type
    if types is not None:
        types = set("".join(types).replace("f", "-"))
    count = 0
    with SquashFsImage.from_file(args.file, args.offset) as image:
        file = image.select(args.path)
        if file is None:
            raise Exception("{} not found".format(args.path))
        if not file.is_dir:
            print_file(file, args.utc, args.show_tz)
            return
        recursive = not args.recursive if args.path == ROOT else args.recursive
        directory = file.riter() if recursive else file
        if types is None:
            for file in directory:
                print_file(file, args.utc, args.show_tz)
                count += 1
        else:
            for file in directory:
                if file.filemode[0] in types:
                    print_file(file, args.utc, args.show_tz)
                    count += 1
    emit("{} file(s) found".format(count))


def scan(args):
    width = 29
    superblocks = find_superblocks(args.file)
    if not superblocks:
        emit("No squashfs 4.0 superblock found")
        return
    for idx, superblock in enumerate(superblocks):
        sblk = argparse.Namespace(**superblock)
        dt = _dtfromts(sblk.mkfs_time, args.utc)
        dtstr = dt if args.show_tz else dt.strftime(DTFMT)
        emit("Superblock #{}".format(idx + 1))
        emit("{:{width}} 0x{:X}".format("Magic:", sblk.s_magic, width=width))
        emit("{:{width}} {}".format("Major:", sblk.s_major, width=width))
        emit("{:{width}} {}".format("Minor:", sblk.s_minor, width=width))
        emit(
            "{:{width}} {}".format("Creation or last append time:", dtstr, width=width)
        )
        emit("{:{width}} {}".format("Size:", sblk.bytes_used, width=width))
        emit(
            "{:{width}} {}".format(
                "Compression:", Compression(sblk.compression).name, width=width
            )
        )
        emit("{:{width}} {}".format("Block size:", sblk.block_size, width=width))
        emit("{:{width}} {}".format("Flags:", sblk.flags, width=width))
        emit(
            "{:{width}} {}".format("Number of fragments:", sblk.fragments, width=width)
        )
        emit("{:{width}} {}".format("Number of inodes:", sblk.inodes, width=width))
        emit("{:{width}} {}".format("Number of ids:", sblk.no_ids, width=width))
        emit(
            "{:{width}} 0x{:X}".format(
                "Inode table start:", sblk.inode_table_start, width=width
            )
        )
        emit(
            "{:{width}} 0x{:X}".format(
                "Directory table start:", sblk.directory_table_start, width=width
            )
        )
        emit(
            "{:{width}} 0x{:X}".format(
                "Fragment table start:", sblk.fragment_table_start, width=width
            )
        )
        emit(
            "{:{width}} 0x{:X}".format(
                "Lookup table start:", sblk.lookup_table_start, width=width
            )
        )
        emit(
            "{:{width}} 0x{:X}".format(
                "ID table start:", sblk.id_table_start, width=width
            )
        )
        emit(
            "{:{width}} 0x{:X}".format(
                "xattr ID table start:", sblk.xattr_id_table_start, width=width
            )
        )
        emit("{:{width}} {}".format("Offset:", sblk.offset, width=width))
        if idx != len(superblocks) - 1:
            emit()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Print information about squashfs images."
    )
    parser.add_argument(
        "-V", "--version", action="version", version="%(prog)s {}".format(__version__)
    )
    subparsers = parser.add_subparsers()  # TODO: required=True Python 3

    pfile = argparse.ArgumentParser(add_help=False)
    pfile.add_argument("file", help="squashfs filesystem")

    poffset = argparse.ArgumentParser(add_help=False)
    poffset.add_argument(
        "-o",
        "--offset",
        type=int,
        default=0,
        help="absolute position of file system's start. Default: %(default)s",
    )

    ptz = argparse.ArgumentParser(add_help=False)
    ptz.add_argument(
        "--utc",
        action="store_true",
        help="use UTC rather than local time zone when displaying time. Default: %(default)s",
    )
    ptz.add_argument(
        "--showtz",
        action="store_true",
        dest="show_tz",
        help="show UTC offset when displaying time. Default: %(default)s",
    )

    helplist = "List the contents of the file system"
    parser_l = subparsers.add_parser(
        "list",
        parents=[pfile, poffset, ptz],
        help=helplist.lower(),
        description=helplist,
    )
    parser_l.add_argument(
        "-p",
        "--path",
        default=ROOT,
        help="absolute path of directory or file to list. Default: %(default)r",
    )
    parser_l.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="whether to list recursively. For the root directory the value is inverted. Default: %(default)s",
    )
    parser_l.add_argument(
        "-t",
        "--type",
        nargs="+",
        metavar="TYPE",
        choices=list("fdlpsbc"),
        help="when listing a directory, filter by file type with %(choices)s",
    )
    parser_l.set_defaults(func=list_)

    helpextr = "Extract files from the file system"
    parser_e = subparsers.add_parser(
        "extract", parents=[pfile, poffset], help=helpextr.lower(), description=helpextr
    )
    parser_e.add_argument(
        "-d",
        "--dest",
        help="directory that will contain the extracted file(s). If it doesn't exist it will be created. Default: current directory",
    )
    parser_e.add_argument(
        "-p",
        "--path",
        default=ROOT,
        help="absolute path of directory or file to extract. Default: %(default)r",
    )
    parser_e.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="overwrite files that already exist. Default: %(default)s",
    )
    parser_e.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="don't print extraction status. Default: %(default)s",
    )
    parser_e.set_defaults(func=extract)

    helpscan = "Find and show all the superblocks that can be found in a file"
    parser_s = subparsers.add_parser(
        "scan", parents=[pfile, ptz], help=helpscan.lower(), description=helpscan
    )
    parser_s.set_defaults(func=scan)

    args = parser.parse_args(argv)
    if "file" not in args:
        parser.error("the following arguments are required: subcommand")
    if not os.path.isfile(args.file):
        emit("error: file does not exist")
        return 2
    if "path" in args and not posixpath.isabs(args.path):
        emit("error: path is not absolute")
        return 2
    if "offset" in args and args.offset is not None and args.offset < 0:
        emit("error: offset cannot be negative")
        return 2

    try:
        args.func(args)
    except Exception as e:
        emit("error: {}".format(e))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
