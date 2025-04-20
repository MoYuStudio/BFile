#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BFile (Binary File) 图像模块
提供图像与BFile格式之间的转换功能
"""

import os
import numpy as np
from PIL import Image as PILImage
import struct
from typing import Optional, Tuple

from .core import (
    encode_run_length, 
    decode_run_length, 
    compress_data, 
    decompress_data,
    Error,
    EncodeError,
    DecodeError,
    FileError
)

class Image:
    @staticmethod
    def png_to_binary(input_path: str, output_path: str, threshold: int = 128) -> bool:
        """
        将PNG图像转换为二进制格式
        
        Args:
            input_path: 输入PNG图像路径
            output_path: 输出文件路径
            threshold: 二值化阈值，默认128
            
        Returns:
            bool: 转换是否成功
        """
        try:
            # 读取图像并转换为灰度图
            img = PILImage.open(input_path).convert('L')
            img_array = np.array(img)
            
            # 二值化处理
            binary = (img_array > threshold).astype(np.uint8)
            
            # 编码为游程长度
            encoded = encode_run_length(binary.flatten())
            
            # 压缩数据
            compressed = compress_data(encoded)
            
            # 写入文件
            with open(output_path, 'wb') as f:
                # 写入文件头
                f.write(struct.pack('>II', img.width, img.height))
                # 写入压缩数据
                f.write(compressed)
                
            return True
            
        except Exception as e:
            raise EncodeError(f"PNG转失败: {str(e)}")

    @staticmethod
    def binary_to_png(input_path: str, output_path: str) -> bool:
        """
        将二进制格式转换为PNG图像
        
        Args:
            input_path: 输入文件路径
            output_path: 输出PNG图像路径
            
        Returns:
            bool: 转换是否成功
        """
        try:
            with open(input_path, 'rb') as f:
                # 读取文件头
                width, height = struct.unpack('>II', f.read(8))
                
                # 读取压缩数据
                compressed = f.read()
                
            # 解压数据
            encoded = decompress_data(compressed)
            
            # 计算总位数
            total_bits = width * height
            
            # 解码游程长度
            binary = decode_run_length(encoded, total_bits)
            
            # 重塑为图像数组
            img_array = np.array(binary).reshape(height, width)
            
            # 转换为PIL图像并保存
            img = PILImage.fromarray(img_array * 255)
            img.save(output_path)
            
            return True
            
        except Exception as e:
            raise DecodeError(f"转PNG失败: {str(e)}")

    @staticmethod
    def bi_to_base64(input_path: str) -> Optional[bytes]:
        """
        将文件转换为base64编码
        
        Args:
            input_path: 文件路径
            
        Returns:
            bytes: base64编码的数据
        """
        try:
            import base64
            with open(input_path, 'rb') as f:
                return base64.b64encode(f.read())
        except Exception as e:
            raise FileError(f"转base64失败: {str(e)}")

    @staticmethod
    def base64_to_bi(base64_data: bytes, output_path: str) -> bool:
        """
        将base64编码转换为文件
        
        Args:
            base64_data: base64编码的数据
            output_path: 输出文件路径
            
        Returns:
            bool: 转换是否成功
        """
        try:
            import base64
            with open(output_path, 'wb') as f:
                f.write(base64.b64decode(base64_data))
            return True
        except Exception as e:
            raise FileError(f"base64转失败: {str(e)}")

if __name__ == "__main__":
    pass