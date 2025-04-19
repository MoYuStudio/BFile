#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BRF (Binary Run-length File) - 一个用于处理二值化图像和视频的Python库
"""

__version__ = "0.1.0"

from .bi import BRFImage as Image
from .bv import BRFVideo as Video
from .core import (
    BRFError,
    BRFEncodeError,
    BRFDecodeError,
    BRFFileError,
    encode_run_length,
    decode_run_length,
    compress_data,
    decompress_data,
    file_to_base64,
    base64_to_file,
    get_file_size_info
)

__all__ = [
    'BRFImage',
    'BRFVideo',
    'BRFError',
    'BRFEncodeError',
    'BRFDecodeError',
    'BRFFileError',
    'encode_run_length',
    'decode_run_length',
    'compress_data',
    'decompress_data',
    'file_to_base64',
    'base64_to_file',
    'get_file_size_info'
]
