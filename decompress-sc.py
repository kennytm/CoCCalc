#!/usr/bin/env python3

import pylzma
import sys
import struct

if len(sys.argv) < 3:
    print("Usage: ./decompress-sc.py [input.sc] [output.scf]")
    exit(0)

with open(sys.argv[1], 'rb') as fin, open(sys.argv[2], 'wb') as fout:
    header = fin.read(5)
    raw_size = fin.read(4)
    size = struct.unpack('<I', raw_size)[0]
    obj = pylzma.decompressobj(maxlength=size)
    fout.write(obj.decompress(header))
    while True:
        chunk = fin.read(4096)
        if not chunk:
            break
        fout.write(obj.decompress(chunk))

    # Sometimes the following line will crash with
    # 'Negative size passed to PyBytes_FromStringAndSize'
    try:
        fout.write(obj.flush())
    except SystemError as e:
        print(e)

# decompress-sc.py --- Decompress CoC SC files.
# Copyright (C) 2013  kennytm
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.


