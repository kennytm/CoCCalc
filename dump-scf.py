#!/usr/bin/env python3

import sys
import struct
import collections
import array
import PIL.Image
import io
import os.path
import itertools

def read_ascii(f):
    size = f.read(1)[0]
    if size == 255:
        return None
    else:
        return f.read(size).decode()

Matrix = collections.namedtuple('Matrix', ('a', 'b', 'c', 'd', 'tx', 'ty'))

ColorTransform = collections.namedtuple('ColorTransform',
                                        ('rm', 'gm', 'bm', 'am', 'ra', 'ga', 'ba'))

Shape = collections.namedtuple('Shape', ('id', 'commands'))

ShapeDrawBitmapCommand = collections.namedtuple('ShapeDrawBitmapCommand',
                                                ('texture', 'xys', 'uvs'))

TextField = collections.namedtuple('TextField', ('id',))

def parse_rgba4444_bitmap(data):
    # TODO: Not sure about the actual order.
    result = bytearray()
    for i in range(0, len(data), 2):
        result.append((data[i+1] >> 4) * 17)
        result.append((data[i+1] & 0xf) * 17)
        result.append((data[i] >> 4) * 17)
        result.append((data[i] & 0xf) * 17)
    return bytes(result)


def parse_rgba5551_bitmap(data):
    raise NotImplementedError()

def parse_rgb565_bitmap(data):
    raise NotImplementedError()

def parse_rgba8888_bitmap(data):
    return data

def parse_la88_bitmap(data):
    raise NotImplementedError()

BITMAP_PARSERS = [parse_rgba4444_bitmap,
                  parse_rgba5551_bitmap,
                  parse_rgb565_bitmap,
                  parse_rgba8888_bitmap,
                  parse_la88_bitmap]

attributes = [
    None,
    'texture',
    'shape',
    'movie_clip',
    None,
    None,
    None,
    'text_field',
    'matrix',
    'color_transform',
    'movie_clip',
    None,
    'movie_clip',
    'timeline_offset',
    'movie_clip',
]


class Scf:
    def __init__(self):
        self.textures = []
        self.movie_clips = []
        self.shapes = []
        self.color_transforms = []
        self.matrixs = []
        self.text_fields = []
        self.timeline_offsets = []


    def parse(self, f):
        f.read(12)  # These are the count of all objects, but we don't need these.
        f.read(5)   # These bytes are just ignored (why 5 bytes...?)

        export_count = struct.unpack('<H', f.read(2))[0]
        export_ids = array.array('H', f.read(2 * export_count))

        export_names = [read_ascii(f) for _ in range(export_count)]
        self.exports = dict(zip(export_ids, export_names))

        while True:
            (tag_type, tag_length) = struct.unpack('<BI', f.read(5))
            if tag_type == 0:
                break

            data = f.read(tag_length)
            attribute = attributes[tag_type]
            result = getattr(self, 'parse_' + attribute)(data, tag_type)
            getattr(self, attributes[tag_type] + 's').append(result)


    @staticmethod
    def parse_matrix(data, tag_type):
        m = struct.unpack('<6i', data)
        return Matrix(a=m[0]/1024, b=m[1]/1024, c=m[2]/1024, d=m[3]/1024,
                      tx=m[4]/-20, ty=m[5]/-20)


    @staticmethod
    def parse_color_transform(data, tag_type):
        ct = struct.unpack('<7B', data)
        return ColorTransform(ra=ct[0], ga=ct[1], ba=ct[2],
                              am=ct[3], rm=ct[4], gm=ct[5], bm=ct[6])


    @staticmethod
    def parse_texture(data, tag_type):
        (sc_type, width, height) = struct.unpack_from('<BHH', data)
        if 2 <= sc_type < 7:
            sc_type -= 2
        else:
            sc_type = 3

        rgba_bytes = BITMAP_PARSERS[sc_type](data[5:])
        image = PIL.Image.frombytes('RGBA', (width, height), rgba_bytes)
        return image


    def parse_shape(self, data, tag_type):
        f = io.BytesIO(data)
        (id_, commands_count) = struct.unpack('<HH', f.read(4))

        commands = []
        for _ in range(commands_count):
            (command_type, length) = struct.unpack('<BI', f.read(5))
            shape_data = f.read(length)

            if command_type == 0:
                break
            elif command_type != 4:
                continue

            (tex_id, *rest) = struct.unpack('<B8I8h', shape_data)
            commands.append(ShapeDrawBitmapCommand(
                texture=self.textures[tex_id],
                xys=((rest[0]/-20, rest[1]/-20),
                     (rest[2]/-20, rest[3]/-20),
                     (rest[4]/-20, rest[5]/-20),
                     (rest[6]/-20, rest[7]/-20)),
                uvs=((rest[8], rest[9]),
                     (rest[10], rest[11]),
                     (rest[12], rest[13]),
                     (rest[14], rest[15]))
            ))

        return Shape(id=id_, commands=commands)


    @staticmethod
    def parse_text_field(data, tag_type):
        # We don't care about text fields.
        return TextField(id=struct.unpack('<H', f.read(2))[0])
        #
        # f = io.BytesIO(data)
        # id_ = struct.unpack('<H', f.read(2))[0]
        # font_name = read_ascii(f)
        # (color, font_prop_2, font_prop_3, is_multiline, x90, align,
        #  font_size, x9c, xa0, xa4, xa8, font_prop_1) = struct.unpack('<I4?2B4H?', f.read(19))
        # text = read_ascii(f)
        # return (id_, font_name, color, font_prop_2, font_prop_3, is_multiline,
        #         x90, align, font_size, x9c, xa0, xa4, xa8, font_prop_1, text)

    def parse_movie_clip(self, data, tag_type):
        return None


if len(sys.argv) < 3:
    print('Usage: ./dump-scf.py [*.scf] [directory]')
    exit(0)

scf = Scf()
directory = sys.argv[2]
exported_regions = set()
with open(sys.argv[1], 'rb') as f:
    scf.parse(f)
    for shape in scf.shapes:
        shape_id = shape.id
        for index, command in enumerate(shape.commands):
            uvs = command.uvs
            min_u = min(uv[0] for uv in uvs)
            max_u = max(uv[0] for uv in uvs)
            min_v = min(uv[1] for uv in uvs)
            max_v = max(uv[1] for uv in uvs)
            if min_u == max_u or min_v == max_v:
                continue
            export_region = (min_u, min_v, max_u, max_v)
            key = (id(command.texture), export_region)
            if key in exported_regions:
                continue
            exported_regions.add(key)
            image = command.texture.crop(export_region)
            name = '{0}.{1}.png'.format(shape_id, index)
            image.save(os.path.join(directory, name))

# dump-scf.py --- Dump images from decompressed SC files.
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

