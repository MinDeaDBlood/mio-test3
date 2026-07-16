#!/usr/bin/env python

"""
Copyright (C) 2016 Elliott Mitchell <ehem+android@m5p.com>

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import print_function
from src.core.diagnostics import emit
from src.core.errors import CoreOperationError

import hashlib
import io
import os
import subprocess
import sys
import zlib
from binascii import crc32
from collections import OrderedDict

import dz

# compatibility, Python 3 has SEEK_HOLE/SEEK_DATA, Python 2 does not
SEEK_HOLE = io.SEEK_HOLE if hasattr(io, "SEEK_HOLE") else 4
SEEK_DATA = io.SEEK_DATA if hasattr(io, "SEEK_DATA") else 3


class EXT4SparseChunk(dz.DZStruct):
    """
    Class for handling chunk from Android sparse image format file
    """

    # Known length of chunk
    _dz_length = 12

    # Doesn't include magic number, this should match output, I hope
    _dz_header = b""

    # Format dictionary
    _dz_format_dict = OrderedDict(
        [
            ("header", ("0s", False)),  # magic number (none)
            ("type", ("H", False)),  # type value
            ("reserved1", ("H", True)),  # reserved
            ("chunkCount", ("I", False)),  # blocks in output
            ("totalSize", ("I", False)),  # bytes of chunk input
        ]
    )

    # Chunk types
    typeRaw = 0xCAC1
    typeFill = 0xCAC2
    typeDontCare = 0xCAC3
    typeCrc32 = 0xCAC4

    def __init__(self, head, buf, pipe, blockShift, readSize):
        """
        Initializer for EXT4SparseChunk, gets DZStruct to fill values
        """
        super(EXT4SparseChunk, self).__init__(EXT4SparseChunk)

        values = self.unpackdict(buf[: self._dz_length])

        self.type = values["type"]
        self.blocks = values["chunkCount"]

        self.remaining = self.blocks << blockShift

        self.readSize = readSize

        self.pipe = pipe

        self.head = head

        if self.type == self.typeRaw:
            # would such a case suggest zero-padding?
            if self.remaining != values["totalSize"] - len(buf):
                raise CoreOperationError(
                    "Raw sparse chunk payload size is invalid", exit_code=64
                )
        elif self.type == self.typeFill:
            buf = self.pipe.read(values["totalSize"] - len(buf))
            self.buffer = b""
            while len(self.buffer) < readSize:
                self.buffer += buf

    def __del__(self):
        """
        Destructor for EXT4SparseChunk, notably read remaining data,
        if any is left behind
        """

        if self.type == self.typeRaw or self.type == self.typeFill:
            while self.remaining > 0:
                if self.remaining < (1 << self.blockShift):
                    buf = self.pipe.read(self.remaining)
                else:
                    buf = self.pipe.read(self.readSize)
                self.remaining -= len(buf)
                self.head.crc = crc32(buf, self.head.crc)

    def __iter__(self):
        """
        The __iter__ method for doing loops
        """
        return self if self.type == self.typeRaw or self.type == self.typeFill else None

    def __next__(self):
        """
        Retrieve the next parsed chunk
        """

        if self.remaining <= 0:
            raise StopIteration

        if self.type == self.typeRaw:
            if self.remaining < self.readSize:
                buf = self.pipe.read(self.remaining)
            else:
                buf = self.pipe.read(self.readSize)

        elif self.type == self.typeFill:
            if self.remaining < self.readSize:
                buf = self.buffer[: self.readSize]
            else:
                buf = self.buffer

        self.remaining -= len(buf)

        self.head.crc = crc32(buf, self.head.crc)

        return buf

    # Python 2 compatibility
    next = __next__


class EXT4SparseFile(dz.DZStruct):
    """
    Class for handling Android sparse image file format
    """

    # Known length of headers
    _dz_length = 28

    # Header magic number
    _dz_header = b"\x3a\xff\x26\xed"

    # Format dictionary
    _dz_format_dict = OrderedDict(
        [
            ("header", ("4s", False)),  # magic number
            ("major", ("H", False)),  # Major version
            ("minor", ("H", False)),  # Minor version
            ("headerSize", ("H", False)),  # Actual size of header
            ("chunkHSize", ("H", False)),  # Chunk header size
            ("blockSize", ("I", False)),  # block size in bytes
            ("totalBlocks", ("I", False)),  # blocks in image
            ("totalChunks", ("I", False)),  # number of chunks
            ("imageCRC32", ("I", False)),  # CRC32 of image
        ]
    )

    def __init__(self, name, readSize):
        """
        Initializer for EXT4SparseHeader, gets DZStruct to fill values
        """
        super(EXT4SparseFile, self).__init__(EXT4SparseFile)

        # Invoke ext2simg (really should be ext4tosimg)
        try:
            child = subprocess.Popen(
                ["ext2simg", "-c", name, "-"], stdout=subprocess.PIPE
            )
        except OSError:
            emit(
                "[!] Failed executing ext2simg, has it been installed?", file=sys.stderr
            )
            emit("[ ]", file=sys.stderr)
            emit(
                "[ ] Suggested resource: http://www.xda-developers.com/easily-get-binaries-needed-to-work-with-kernels/",
                file=sys.stderr,
            )
            hint = (
                " Install android-tools-fsutils on Debian/Linux."
                if os.name != "nt"
                else ""
            )
            raise FileNotFoundError(f"ext2simg executable is unavailable.{hint}")

        self.child = child

        self.readSize = readSize

        # grab the header
        buf = self.child.stdout.read(self._dz_length)

        # parse out the values
        values = self.unpackdict(buf)

        # valid, the format hasn't changed?
        if values is None:
            raise CoreOperationError(
                "Invalid sparse image header from ext2simg", exit_code=1
            )

        # Newer format, fail if not known
        if values["major"] != 1:
            raise CoreOperationError(
                "Unsupported sparse image major version", exit_code=1
            )

        # Newer format, but not incompatible
        if values["minor"] > 0:
            emit(
                "[!] Warning: Output format from ext2simg more recent than this utility",
                file=sys.stderr,
            )

        # Extra fields to ignore
        if values["headerSize"] > self._dz_length:
            self.child.stdout.read(values["headerSize"] - self._dz_length)

        # How large the chunks are
        self.chunkHSize = values["chunkHSize"]
        self.chunkCount = values["totalChunks"]

        # CRC32 of image
        self.origCrc = values["imageCRC32"]
        self.crc = crc32(b"")

        # Block size of the device, power of 2, minimum of 4K
        size = values["blockSize"]
        self.blockSize = size

        if size & (size - 1):
            raise CoreOperationError(
                "Sparse image block size is not a power of two", exit_code=1
            )

        result = 0
        shift = 32
        while shift > 0:
            if (size >> shift) > 0:
                size >>= shift
                result += shift
            shift >>= 1
        self.blockShift = result

    def __del__(self):
        """
        Destructor for Image2Chunks, notably kills child if needed
        """

        if hasattr(self, "child") and self.child is not None:
            # normal exit
            if self.chunkCount <= 0:
                if self.child.poll() is not None:
                    if self.child.returncode > 0:
                        emit(
                            "[!] Warning: Return code of {:d} from ext2simg!".format(
                                self.child.returncode
                            ),
                            file=sys.stderr,
                        )
                    elif self.child.returncode < 0:
                        emit(
                            "[!] Warning ext2simg killed by signal {:d}!".format(
                                -self.child.returncode
                            ),
                            file=sys.stderr,
                        )
                # otherwise 0 exit, no problem

                # hasn't terminated, trouble...
                else:
                    self.child.terminate()
                    if self.child.wait(10) is None:
                        self.child.kill()
                    emit("[!] Warning forced to terminate ext2simg", file=sys.stderr)
            # abnormal condition of some sort
            else:
                self.child.terminate()
                if self.child.wait(10) is None:
                    self.child.kill()

    def __iter__(self):
        """
        The __iter__ method for doing loops
        """
        return self

    def __next__(self):
        """
        Retrieve the next parsed chunk
        """

        try:
            # The previous chunk object *MUST* be destroyed *NOW*
            self.last.__del__()
        except AttributeError:
            # doesn't exist yet
            pass

        if self.chunkCount <= 0:
            self.crc = self.crc & 0xFFFFFFFF
            # apparently 0 is used for none computed
            if self.crc != self.origCrc and self.origCrc != 0:
                raise CoreOperationError(
                    f"Sparse image CRC mismatch: computed={self.crc:08X}, original={self.origCrc:08X}",
                    exit_code=4,
                )

            raise StopIteration

        self.chunkCount -= 1

        buf = self.child.stdout.read(self.chunkHSize)

        if len(buf) != self.chunkHSize:
            raise CoreOperationError(
                "Short read while reading sparse chunk header", exit_code=2
            )

        self.last = EXT4SparseChunk(
            self, buf, self.child.stdout, self.blockShift, self.readSize
        )
        return self.last

    # Python 2 compatibility
    next = __next__


class Image2Chunks(dz.DZChunk):
    """
    Class for transforming a single file from a raw image into chunk files
    """

    def openFiles(self, name):
        """
        Opens the files, provide an error message if one doesn't exist
        """

        try:
            role = "parameter"
            self.paramsFile = io.open(name + ".params", "rt")
            role = "image"
            self.file = io.FileIO(name, "rb")

        except OSError as exc:
            raise FileNotFoundError(f"Failed opening {name} for {role}") from exc

    def loadParams(self, name):
        """
        Loads the .params file for image, saves off key values
        """

        params = dict()
        line = self.paramsFile.readline()
        while len(line) > 0:
            line.lstrip()
            line = line.partition("#")[0]
            if len(line) == 0:
                line = self.paramsFile.readline()
                continue
            parts = line.partition("=")
            if len(parts[1]) == 0:
                emit(
                    "[!] Bad line in {:s}'s parameter file".format(name),
                    file=sys.stderr,
                )
            var = parts[0].rstrip()
            # currently we only have integers in the file
            val = int(parts[2].strip())
            params[var] = val
            line = self.paramsFile.readline()

        self.paramsFile.close()
        del self.paramsFile

        if "phantom" in params and params["phantom"]:
            emit("[!] {:s} is a phantom slice, skipping!".format(name))
            return False

        for k in "blockShift", "startLBA", "endLBA", "lastWipe", "dev":
            if k not in params:
                raise CoreOperationError(
                    f"Missing image chunk parameter: {k}", exit_code=1
                )

        self.blockShift = params["blockShift"]
        self.blockSize = 1 << self.blockShift
        self.startLBA = params["startLBA"]
        self.endLBA = params["endLBA"]
        self.lastWipe = params["lastWipe"]
        self.dev = params["dev"]

        return True

    def makeChunksHoles(self, name):
        """
        Generate one or more .chunks files for the named file
        """

        os.chdir(os.path.dirname(name))
        name = os.path.basename(name)
        baseName = name.rpartition(".")[0] + "_"
        sliceName = name.rpartition(".")[0].encode("utf8")

        current = 0
        targetAddr = self.startLBA
        eof = self.file.seek(0, io.SEEK_END)
        self.file.seek(0, io.SEEK_SET)

        while current < eof:
            hole = (self.file.seek(current, SEEK_HOLE) + self.blockSize - 1) & ~(
                self.blockSize - 1
            )
            # Python's handling of this condition is suboptimal
            try:
                next = self.file.seek(hole, SEEK_DATA) & ~(self.blockSize - 1)
                trimCount = (next - current) >> self.blockShift
            except IOError:
                next = eof
                trimCount = self.lastWipe - targetAddr

            # Watch out for chunks >4GB (too big!)
            # Also, try not to test the limits of LG's tools...
            if (hole - current) >= 1 << 27:
                hole = current + (1 << 27)
                next = hole
                trimCount = (next - current) >> self.blockShift

            md5 = hashlib.md5()
            crc = crc32(b"")
            zobj = zlib.compressobj(1)
            self.file.seek(current, io.SEEK_SET)

            chunkName = baseName + str(targetAddr) + ".bin"
            out = io.FileIO(chunkName + ".chunk", "wb")

            emit(
                "[+] Compressing {:s} to {:s} ({:d} empty blocks)".format(
                    name, chunkName, (next - hole) >> self.blockShift
                )
            )

            chunkName = chunkName.encode("utf8")
            out.seek(self._dz_length, io.SEEK_SET)
            zlen = 0

            for b in range((hole - current) >> self.blockShift):
                buf = self.file.read(self.blockSize)
                md5.update(buf)
                crc = crc32(buf, crc)
                zdata = zobj.compress(buf)
                zlen += len(zdata)
                out.write(zdata)

            zdata = zobj.flush(zlib.Z_FINISH)
            zlen += len(zdata)
            out.write(zdata)
            md5 = md5.digest()

            out.seek(0, io.SEEK_SET)

            values = {
                "sliceName": sliceName,
                "chunkName": chunkName,
                "targetSize": hole - current,
                "dataSize": zlen,
                "md5": md5,
                "targetAddr": targetAddr,
                "trimCount": trimCount,
                "crc32": crc & 0xFFFFFFFF,
                "dev": self.dev,
            }

            header = self.packdict(values)
            out.write(header)
            out.close()

            current = next
            targetAddr = self.startLBA + (current >> self.blockShift)

        emit("[+] done\n")

    def makeChunksEXT4FS(self, name):
        """
        Generate one or more .chunks files assuming an EXT4 FS
        """

        os.chdir(os.path.dirname(name))
        name = os.path.basename(name)
        baseName = name.rpartition(".")[0] + "_"
        sliceName = name.rpartition(".")[0].encode("utf8")

        # Check length before closing
        self.file.seek(0, io.SEEK_END)

        # Alas, ext2simg can't take the image as stdin
        self.file.close()

        sparse = EXT4SparseFile(name, 1 << self.blockShift)

        # sigh, Python 2 hack for some variables
        class nl:
            yuck = "truly"

        nl.current = 0
        nl.targetAddr = self.startLBA
        nl.trimCount = 0

        # local function not used by anyone else
        def complete():
            # nonlocal zlen, md5, current, targetAddr, trimCount
            zdata = zobj.flush(zlib.Z_FINISH)
            nl.zlen += len(zdata)
            out.write(zdata)
            nl.md5 = nl.md5.digest()

            out.seek(0, io.SEEK_SET)

            values = {
                "sliceName": sliceName,
                "chunkName": chunkName,
                "targetSize": dataBlocks << self.blockShift,
                "dataSize": nl.zlen,
                "md5": nl.md5,
                "targetAddr": nl.targetAddr,
                "trimCount": nl.trimCount,
                "crc32": crc & 0xFFFFFFFF,
                "dev": self.dev,
            }

            nl.header = self.packdict(values)
            out.write(nl.header)
            out.close()

            nl.current += nl.trimCount << self.blockShift
            nl.targetAddr = self.startLBA + (nl.current >> self.blockShift)

            emit("({:d} empty blocks)".format(nl.trimCount - dataBlocks))

            nl.trimCount = 0

        for chunk in sparse:
            if (
                chunk.type == EXT4SparseChunk.typeRaw
                or chunk.type == EXT4SparseChunk.typeFill
            ):
                if nl.trimCount:
                    complete()
                dataBlocks = chunk.remaining >> self.blockShift
                nl.trimCount += dataBlocks

                nl.md5 = hashlib.md5()
                crc = crc32(b"")
                zobj = zlib.compressobj(1)

                chunkName = baseName + str(nl.targetAddr) + ".bin"
                out = io.FileIO(chunkName + ".chunk", "wb")

                sys.stdout.write(
                    "[+] Compressing {:s} to {:s} ".format(name, chunkName)
                )

                chunkName = chunkName.encode("utf8")
                out.seek(self._dz_length, io.SEEK_SET)
                nl.zlen = 0

                for buf in chunk:
                    nl.md5.update(buf)
                    crc = crc32(buf, crc)
                    zdata = zobj.compress(buf)
                    nl.zlen += len(zdata)
                    out.write(zdata)

            elif chunk.type == EXT4SparseChunk.typeDontCare:
                # check for EOF, lastWipe overrides
                if sparse.chunkCount == 0:
                    nl.trimCount = self.lastWipe - nl.targetAddr
                else:
                    nl.trimCount += chunk.remaining >> self.blockShift
                complete()

            elif chunk.type == EXT4SparseChunk.typeCrc32:
                pass
            else:
                raise CoreOperationError(
                    f"Unknown sparse chunk type: 0x{chunk.type:04X}", exit_code=64
                )

        if nl.trimCount:
            nl.trimCount = self.lastWipe - nl.targetAddr
            complete()

        emit("[+] done\n")

    def makeChunksProbe(self, name):
        """
        Generate one or more .chunks files for the named file
        """

        os.chdir(os.path.dirname(name))
        name = os.path.basename(name)
        baseName = name.rpartition(".")[0] + "_"
        sliceName = name.rpartition(".")[0].encode("utf8")

        current = 0
        targetAddr = self.startLBA
        eof = self.file.seek(0, io.SEEK_END)
        self.file.seek(0, io.SEEK_SET)

        # emulate characteristics of LG's tool, always find a block at start
        readSize = self.blockSize << 10

        md5 = hashlib.md5()
        crc = crc32(b"")
        zobj = zlib.compressobj(1)
        self.file.seek(current, io.SEEK_SET)

        chunkName = baseName + str(targetAddr) + ".bin"
        out = io.FileIO(chunkName + ".chunk", "wb")

        sys.stdout.write("[+] Compressing {:s} to {:s} ".format(name, chunkName))

        chunkName = chunkName.encode("utf8")
        out.seek(self._dz_length, io.SEEK_SET)
        zlen = 0

        wipeData = readSize
        dataCount = readSize

        buf = self.file.read(readSize)

        while len(buf.lstrip(b"\x00")) == 0 and current < eof:
            md5.update(buf)
            crc = crc32(buf, crc)
            zdata = zobj.compress(buf)
            zlen += len(zdata)
            out.write(zdata)
            wipeData += readSize
            dataCount += readSize
            current += readSize

            buf = self.file.read(readSize)

        while current < eof:
            while len(buf.lstrip(b"\x00")) != 0 and current < eof:
                md5.update(buf)
                crc = crc32(buf, crc)
                zdata = zobj.compress(buf)
                zlen += len(zdata)
                out.write(zdata)
                wipeData += readSize
                dataCount += readSize
                current += readSize

                buf = self.file.read(readSize)

            zdata = zobj.flush(zlib.Z_FINISH)
            zlen += len(zdata)
            out.write(zdata)
            md5 = md5.digest()

            while len(buf.lstrip(b"\x00")) == 0 and current < eof:
                wipeData += readSize
                current += readSize
                buf = self.file.read(readSize)

            emit(
                "({:d} empty blocks)".format((wipeData - dataCount) >> self.blockShift)
            )

            out.seek(0, io.SEEK_SET)

            values = {
                "sliceName": sliceName,
                "chunkName": chunkName,
                "targetSize": dataCount,
                "dataSize": zlen,
                "md5": md5,
                "targetAddr": targetAddr,
                "trimCount": wipeData >> self.blockShift,
                "crc32": crc & 0xFFFFFFFF,
                "dev": self.dev,
            }

            header = self.packdict(values)
            out.write(header)
            out.close()

            targetAddr = self.startLBA + (current >> self.blockShift)

            if current < eof:
                md5 = hashlib.md5()
                crc = crc32(b"")
                zobj = zlib.compressobj(1)

                chunkName = baseName + str(targetAddr) + ".bin"
                out = io.FileIO(chunkName + ".chunk", "wb")

                sys.stdout.write(
                    "[+] Compressing {:s} to {:s} ".format(name, chunkName)
                )

                chunkName = chunkName.encode("utf8")
                out.seek(self._dz_length, io.SEEK_SET)
                zlen = 0

                wipeData = readSize
                dataCount = readSize

        emit("[+] done\n")

    def __init__(self, name, strategy):
        """
        Initializer for Image2Chunks class, takes filename as arg
        """

        super(Image2Chunks, self).__init__()

        self.openFiles(name)

        if self.loadParams(name):
            if strategy == 0:
                self.makeChunksEXT4FS(name)
            elif strategy == 1:
                self.makeChunksHoles(name)
            elif strategy == 2:
                self.makeChunksProbe(name)
            elif strategy is None:
                raise CoreOperationError(
                    "No image chunk strategy was specified", exit_code=1
                )
            else:
                raise CoreOperationError(
                    "Internal image chunk strategy error", exit_code=127
                )


def print_help(progname: str) -> None:
    emit(
        "usage: {:s} [-h | --help] [-e | --ext4 | -s | --sparse | -p | --probe] <file(s)>\n".format(
            progname
        )
    )
    emit("DZ Chunking program by Elliott Mitchell\n")
    emit("optional arguments:")
    emit("  -h | --help           show this help message and exit")
    emit("  -e | --ext4           use Android's sparse EXT4 dump utility (recommended)")
    emit("  -s | --sparse         use SEEK_DATA/SEEK_HOLE (not available on all OSes)")
    emit("  -p | --probe          probe for holes (safe)")


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    progname = sys.argv[0]
    basedir = os.open(".", os.O_DIRECTORY)
    strategy = None

    if not args:
        print_help(progname)
        return 0

    try:
        for arg in args:
            if arg.startswith("-"):
                if arg in ("-e", "--ext4"):
                    strategy = 0
                elif arg in ("-s", "--sparse"):
                    strategy = 1
                elif arg in ("-p", "--probe"):
                    strategy = 2
                elif arg in ("-h", "--help"):
                    print_help(progname)
                    return 0
                else:
                    emit('[!] Unknown option "{:s}"'.format(arg))
                    return 1
                continue

            Image2Chunks(arg, strategy)
            os.fchdir(basedir)
    except CoreOperationError as error:
        emit(str(error))
        return error.exit_code if error.exit_code is not None else 1
    finally:
        os.close(basedir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
