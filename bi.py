#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import numpy as np
from PIL import Image
import struct
import base64

def encode_run_length(data):
    """
    使用改进的游程编码压缩数据
    返回压缩后的字节数组，格式为：
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

def decode_run_length(data, total_bits):
    """
    解压改进的游程编码的数据
    返回解压后的数组
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

def png_to_binary(input_path, output_path, threshold=128):
    """
    将PNG图片转换为高度压缩的二值化图像
    使用改进的游程编码和位压缩
    
    参数:
        input_path: 输入PNG图片路径
        output_path: 输出压缩文件路径
        threshold: 二值化阈值，默认为128
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"输入文件不存在: {input_path}")
    
    if not input_path.lower().endswith('.png'):
        raise ValueError("输入文件必须是PNG格式")
    
    try:
        img = Image.open(input_path).convert('L')
        width, height = img.size
        img_array = np.array(img)
        # 二值化处理（0表示黑，1表示白）
        binary_array = (img_array >= threshold).astype(np.uint8)
        flat_array = binary_array.flatten()
        
        # 使用改进的游程编码压缩数据
        compressed_data = encode_run_length(flat_array)
        
        # 使用zlib进一步压缩数据
        import zlib
        compressed_data = zlib.compress(compressed_data)
        
        with open(output_path, 'wb') as f:
            # 写入宽度和高度信息
            f.write(struct.pack('>HH', width, height))
            # 写入压缩后的数据
            f.write(compressed_data)
        
        print(f"转换成功: {input_path} -> {output_path}")
        print(f"原始大小: {os.path.getsize(input_path)} 字节")
        print(f"压缩后大小: {os.path.getsize(output_path)} 字节")
        print(f"压缩率: {(1 - os.path.getsize(output_path) / os.path.getsize(input_path)) * 100:.2f}%")
        return True
    
    except Exception as e:
        print(f"转换失败: {str(e)}")
        return False

def binary_to_png(input_path, output_path):
    """
    将压缩的二值化图像转换回PNG格式
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"输入文件不存在: {input_path}")
    
    if not output_path.lower().endswith('.png'):
        output_path += '.png'
    
    try:
        with open(input_path, 'rb') as f:
            # 读取宽度和高度信息
            width, height = struct.unpack('>HH', f.read(4))
            # 读取压缩后的数据
            compressed_data = f.read()
        
        # 使用zlib解压数据
        import zlib
        decompressed_data = zlib.decompress(compressed_data)
        
        # 计算总位数
        total_bits = width * height
        
        # 解压数据
        flat_array = decode_run_length(decompressed_data, total_bits)
        
        # 将一维数组重塑为二维数组
        img_array = flat_array.reshape(height, width)
        
        # 将0和1转换为0和255
        img_array = img_array * 255
        
        # 创建图片
        img = Image.fromarray(img_array)
        img.save(output_path)
        
        print(f"转换成功: {input_path} -> {output_path}")
        return True
    
    except Exception as e:
        print(f"转换失败: {str(e)}")
        return False

def bi_to_base64(input_path):
    """
    将BI格式文件转换为base64编码
    
    参数:
        input_path: 输入BI文件路径
    返回:
        base64编码的字符串
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"输入文件不存在: {input_path}")
    
    try:
        with open(input_path, 'rb') as f:
            data = f.read()
        return base64.b64encode(data)
    except Exception as e:
        print(f"转换失败: {str(e)}")
        return None

def base64_to_bi(base64_data, output_path):
    """
    将base64编码的数据转换回BI格式
    
    参数:
        base64_data: base64编码的数据
        output_path: 输出BI文件路径
    返回:
        是否转换成功
    """
    try:
        data = base64.b64decode(base64_data)
        with open(output_path, 'wb') as f:
            f.write(data)
        print(f"转换成功: base64数据 -> {output_path}")
        return True
    except Exception as e:
        print(f"转换失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 测试PNG到BI的转换
    png_to_binary("1.png", "1.bi", threshold=128)
    
    # 测试BI到PNG的转换
    binary_to_png("1.bi", "1_back.png")
    
    # 测试BI到base64的转换
    base64_data = bi_to_base64("1.bi")
    if base64_data:
        print(f"Base64编码长度: {len(base64_data)}")
    
    # 测试base64到BI的转换
    if base64_data:
        base64_to_bi(base64_data, "1_from_base64.bi")
        # 验证转换后的文件是否可以正确转换为PNG
        binary_to_png("1_from_base64.bi", "1_from_base64.png")