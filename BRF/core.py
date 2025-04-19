#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BRF (Binary Run-length File) 核心模块
提供BRF格式的基础功能，包括编码、解码和文件操作
"""

import os
import numpy as np
import struct
import zlib
import base64
from typing import Tuple, List, Optional, Union, BinaryIO


class BRFError(Exception):
    """BRF格式相关错误的基类"""
    pass


class BRFEncodeError(BRFError):
    """编码过程中的错误"""
    pass


class BRFDecodeError(BRFError):
    """解码过程中的错误"""
    pass


class BRFFileError(BRFError):
    """文件操作相关的错误"""
    pass


def encode_run_length(data: np.ndarray) -> bytearray:
    """
    使用改进的游程编码压缩数据
    
    参数:
        data: 要压缩的二值化数据数组
        
    返回:
        压缩后的字节数组，格式为：
        - 第一个字节：起始位（0或1）
        - 后续字节：每个字节的高4位表示连续个数，低4位表示当前位值
    """
    if len(data) == 0:
        return bytearray([0])

    result = bytearray()
    # 记录起始位
    start_bit = data[0]
    result.append(start_bit)

    count = 1
    current = data[0]

    for i in range(1, len(data)):
        if data[i] == current and count < 15:  # 使用4位存储计数，最大15
            count += 1
        else:
            # 将计数和当前位值打包到一个字节中
            packed = (count << 4) | current
            result.append(packed)
            current = data[i]
            count = 1

    # 添加最后一组计数
    packed = (count << 4) | current
    result.append(packed)
    return result


def decode_run_length(data: bytes, total_bits: int) -> np.ndarray:
    """
    解压改进的游程编码的数据
    
    参数:
        data: 压缩后的数据
        total_bits: 解压后应该有的总位数
        
    返回:
        解压后的二值化数组
    """
    if len(data) == 0:
        return np.array([], dtype=np.uint8)

    result = []
    start_bit = data[0]
    current = start_bit

    # 从第二个字节开始解码
    for i in range(1, len(data)):
        packed = data[i]
        count = (packed >> 4) & 0xF  # 获取高4位的计数
        current = packed & 0xF  # 获取低4位的当前位值
        result.extend([current] * count)

    # 确保解压后的数据长度正确
    if len(result) > total_bits:
        result = result[:total_bits]
    elif len(result) < total_bits:
        # 如果长度不够，用最后一个位填充
        result.extend([current] * (total_bits - len(result)))

    return np.array(result, dtype=np.uint8)


def compress_data(data: bytes) -> bytes:
    """
    使用zlib压缩数据
    
    参数:
        data: 要压缩的数据
        
    返回:
        压缩后的数据
    """
    return zlib.compress(data)


def decompress_data(data: bytes) -> bytes:
    """
    使用zlib解压数据
    
    参数:
        data: 要解压的数据
        
    返回:
        解压后的数据
    """
    return zlib.decompress(data)


def file_to_base64(file_path: str) -> Optional[bytes]:
    """
    将文件转换为base64编码
    
    参数:
        file_path: 文件路径
        
    返回:
        base64编码的数据，失败时返回None
    """
    if not os.path.exists(file_path):
        raise BRFFileError(f"文件不存在: {file_path}")

    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data)
    except Exception as e:
        raise BRFFileError(f"文件转base64失败: {str(e)}")


def base64_to_file(base64_data: Union[str, bytes], output_path: str) -> bool:
    """
    将base64编码的数据保存为文件
    
    参数:
        base64_data: base64编码的数据
        output_path: 输出文件路径
        
    返回:
        是否成功
    """
    try:
        if isinstance(base64_data, str):
            data = base64.b64decode(base64_data)
        else:
            data = base64.b64decode(base64_data)
            
        with open(output_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        raise BRFFileError(f"base64转文件失败: {str(e)}")


def get_file_size_info(input_path: str, output_path: str) -> Tuple[int, int, float]:
    """
    获取文件大小信息和压缩率
    
    参数:
        input_path: 输入文件路径
        output_path: 输出文件路径
        
    返回:
        (原始大小, 压缩后大小, 压缩率)
    """
    input_size = os.path.getsize(input_path)
    output_size = os.path.getsize(output_path)
    compression_ratio = (1 - output_size / input_size) * 100
    return input_size, output_size, compression_ratio