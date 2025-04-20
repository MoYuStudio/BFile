#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BFile (Binary File) 核心模块
提供BFile格式的基础功能，包括编码、解码和文件操作
"""

import os
import numpy as np
import struct
import base64
from typing import Tuple, List, Optional, Union, BinaryIO


class Error(Exception):
    """BFile格式相关错误的基类"""
    pass


class EncodeError(Error):
    """编码过程中的错误"""
    pass


class DecodeError(Error):
    """解码过程中的错误"""
    pass


class FileError(Error):
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


def lz77_compress(data: bytes, window_size: int = 8192, min_match: int = 4) -> bytes:
    """
    使用优化的LZ77算法压缩数据
    
    参数:
        data: 要压缩的数据
        window_size: 滑动窗口大小
        min_match: 最小匹配长度
        
    返回:
        压缩后的数据
    """
    if not data:
        return b''
    
    result = bytearray()
    data_len = len(data)
    pos = 0
    
    # 使用位操作来存储标志位
    flag_byte = 0
    flag_pos = 0
    flag_byte_pos = 0
    
    while pos < data_len:
        # 每8个操作后写入一个标志字节
        if flag_pos == 0:
            flag_byte_pos = len(result)
            result.append(0)  # 占位，稍后更新
        
        # 确定搜索窗口的范围
        window_start = max(0, pos - window_size)
        window_end = pos
        
        # 在窗口中寻找最长匹配
        best_match_length = 0
        best_match_offset = 0
        
        # 从窗口末尾开始搜索，这样可以找到最近的匹配
        for i in range(window_end - 1, window_start - 1, -1):
            match_length = 0
            # 计算匹配长度
            while (pos + match_length < data_len and 
                   i + match_length < window_end and 
                   data[pos + match_length] == data[i + match_length] and 
                   match_length < 255):  # 限制匹配长度为255
                match_length += 1
            
            if match_length > best_match_length:
                best_match_length = match_length
                best_match_offset = pos - i
        
        # 如果找到足够长的匹配
        if best_match_length >= min_match:
            # 设置标志位为1，表示这是一个匹配
            flag_byte |= (1 << flag_pos)
            
            # 编码为(偏移量, 长度)对
            offset = best_match_offset
            length = best_match_length
            
            # 使用可变长度编码存储偏移量和长度
            # 对于小偏移量使用更少的位
            if offset < 64:
                result.append(offset)
            else:
                result.append(0x40 | ((offset >> 8) & 0x3F))
                result.append(offset & 0xFF)
            
            # 对于小长度使用更少的位
            if length < 16:
                result.append(length)
            else:
                result.append(0x10 | (length >> 4))
                result.append(length & 0xFF)
            
            pos += length
        else:
            # 没有找到匹配，直接存储当前字节
            result.append(data[pos])
            pos += 1
        
        # 更新标志位位置
        flag_pos = (flag_pos + 1) % 8
        
        # 如果已经处理了8个操作，更新标志字节
        if flag_pos == 0:
            result[flag_byte_pos] = flag_byte
            flag_byte = 0
    
    # 处理最后不足8个操作的情况
    if flag_pos != 0:
        result[flag_byte_pos] = flag_byte
    
    return bytes(result)


def lz77_decompress(data: bytes) -> bytes:
    """
    解压优化的LZ77压缩的数据
    
    参数:
        data: 要解压的数据
        
    返回:
        解压后的数据
    """
    if not data:
        return b''
    
    result = bytearray()
    pos = 0
    data_len = len(data)
    flag_pos = 0
    
    while pos < data_len:
        # 读取标志字节
        if flag_pos == 0:
            flag_byte = data[pos]
            pos += 1
        
        # 检查当前操作的类型
        is_match = (flag_byte & (1 << flag_pos)) != 0
        flag_pos = (flag_pos + 1) % 8
        
        if is_match:
            # 读取偏移量
            offset_byte = data[pos]
            pos += 1
            
            if offset_byte < 64:
                offset = offset_byte
            else:
                offset_high = offset_byte & 0x3F
                offset_low = data[pos]
                pos += 1
                offset = (offset_high << 8) | offset_low
            
            # 读取长度
            length_byte = data[pos]
            pos += 1
            
            if length_byte < 16:
                length = length_byte
            else:
                length_high = length_byte & 0x0F
                length_low = data[pos]
                pos += 1
                length = (length_high << 4) | length_low
            
            # 从已解压的数据中复制匹配的数据
            start = len(result) - offset
            for i in range(length):
                if start + i < len(result):
                    result.append(result[start + i])
        else:
            # 直接读取原始字节
            if pos < data_len:
                result.append(data[pos])
                pos += 1
    
    return bytes(result)


def compress_data(data: bytes) -> bytes:
    """
    压缩数据（使用优化的LZ77算法替代zlib）
    
    参数:
        data: 要压缩的数据
        
    返回:
        压缩后的数据
    """
    # 使用优化的LZ77算法压缩数据
    return lz77_compress(data)


def decompress_data(data: bytes) -> bytes:
    """
    解压数据（使用优化的LZ77算法替代zlib）
    
    参数:
        data: 要解压的数据
        
    返回:
        解压后的数据
    """
    # 使用优化的LZ77算法解压数据
    return lz77_decompress(data)


def file_to_base64(file_path: str) -> Optional[bytes]:
    """
    将文件转换为base64编码
    
    参数:
        file_path: 文件路径
        
    返回:
        base64编码的数据，失败时返回None
    """
    if not os.path.exists(file_path):
        raise FileError(f"文件不存在: {file_path}")

    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data)
    except Exception as e:
        raise FileError(f"文件转base64失败: {str(e)}")


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
        raise FileError(f"base64转文件失败: {str(e)}")


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