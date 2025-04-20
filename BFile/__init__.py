#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BFile (Binary File) - 一个用于处理二值化图像和视频的Python库
"""

__version__ = "0.1.0"

from .bi import Image as Image
from .bv import Video as Video
from .core import (
    Error,
    EncodeError,
    DecodeError,
    FileError,
    encode_run_length,
    decode_run_length,
    compress_data,
    decompress_data,
    file_to_base64,
    base64_to_file,
    get_file_size_info
)

__all__ = [
    'Image',
    'Video',
    'Error',
    'EncodeError',
    'DecodeError',
    'FileError',
    'encode_run_length',
    'decode_run_length',
    'compress_data',
    'decompress_data',
    'file_to_base64',
    'base64_to_file',
    'get_file_size_info'
]
