#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BFile Micro - BFile图片显示模块
用于在PicoPi的OLED显示屏上显示BFile.bi格式的图片
支持图片加载、显示、动画播放等功能
"""

import struct
import time
import os
from machine import Pin, SPI
import framebuf

from BFile_Micro.color import Color

class BI:
    """BFile图片显示类，用于在OLED显示屏上显示BFile.bi格式的图片"""
    
    def __init__(self, oled_display):
        """
        初始化BFile图片显示类
        
        参数:
            oled_display: OLED显示对象，必须是framebuf.FrameBuffer的子类
        """
        self.oled = oled_display
        self.width = oled_display.width
        self.height = oled_display.height
        
    def decode_run_length(self, data, total_bits):
        """
        解压改进的游程编码的数据
        
        参数:
            data: 压缩后的数据
            total_bits: 解压后应该有的总位数
            
        返回:
            解压后的二值化数组
        """
        if len(data) == 0:
            return []
            
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
            
        return result
        
    def lz77_decompress(self, data):
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
        
    def decompress_data(self, data):
        """
        解压数据
        
        参数:
            data: 要解压的数据
            
        返回:
            解压后的数据
        """
        # 使用优化的LZ77算法解压数据
        return self.lz77_decompress(data)
        
    def load_bi_image(self, bi_path):
        """
        加载BFile.bi格式的图片
        
        参数:
            bi_path: BFile.bi文件路径
            
        返回:
            (width, height, binary_data): 图片宽度、高度和二值化数据
        """
        try:
            # 检查文件是否存在
            try:
                with open(bi_path, "rb") as f:
                    # 读取文件头
                    header = f.read(8)
                    if len(header) < 8:
                        print(f"Error: Incomplete file header: {len(header)} bytes")
                        return None, None, None
                        
                    width, height = struct.unpack('>II', header)
                    
                    # 读取压缩数据
                    compressed = f.read()
            except OSError:
                print(f"Error: File not found: {bi_path}")
                return None, None, None
                
            # 解压数据
            encoded = self.decompress_data(compressed)
            
            # 计算总位数
            total_bits = width * height
            
            # 解码游程长度
            binary = self.decode_run_length(encoded, total_bits)
            
            return width, height, binary
            
        except Exception as e:
            print(f"Error: Failed to load BFile.bi image: {str(e)}")
            return None, None, None
            
    def display_bi_image(self, bi_path, x=0, y=0, scale=1, color=Color.WHITE, bg_color=Color.BLACK):
        """
        在OLED显示屏上显示BFile.bi格式的图片
        
        参数:
            bi_path: BFile.bi文件路径
            x: 显示位置的x坐标
            y: 显示位置的y坐标
            scale: 缩放比例，默认为1
            color: 图片颜色，默认为白色
            bg_color: 背景颜色，默认为黑色
            
        返回:
            bool: 是否成功显示
        """
        try:
            # 加载图片
            width, height, binary = self.load_bi_image(bi_path)
            if width is None or height is None or binary is None:
                print("Error: Failed to load image, cannot display")
                return False
                
            # 检查图片尺寸是否超过屏幕
            if width * scale > self.width or height * scale > self.height:
                print(f"Error: Image size ({width}x{height}) is too large to display")
                return False
                
            # 清屏
            self.oled.fill(bg_color)
            self.oled.show()  # 确保清屏生效
            
            # 使用draw_pixels方法绘制图片
            pixels = []
            pixel_count = 0
            
            for i in range(height):
                for j in range(width):
                    pixel = binary[i * width + j]
                    if pixel == 1:  # 明确检查像素值是否为1
                        if scale > 1:
                            # 如果设置了缩放，则添加多个像素
                            for si in range(scale):
                                for sj in range(scale):
                                    pixels.append((x + j * scale + sj, y + i * scale + si, color))
                        else:
                            pixels.append((x + j, y + i, color))
                        pixel_count += 1
                    elif bg_color != Color.BLACK:
                        if scale > 1:
                            # 如果设置了缩放，则添加多个像素
                            for si in range(scale):
                                for sj in range(scale):
                                    pixels.append((x + j * scale + sj, y + i * scale + si, bg_color))
                        else:
                            pixels.append((x + j, y + i, bg_color))
            
            # 批量绘制像素
            if hasattr(self.oled, 'draw_pixels'):
                self.oled.draw_pixels(pixels)
            else:
                # 如果不支持批量绘制，则逐个绘制
                for px, py, pc in pixels:
                    self.oled.pixel(px, py, pc)
            
            # 更新显示
            self.oled.show()
            return True
            
        except Exception as e:
            print(f"Error: Failed to display BFile.bi image: {str(e)}")
            return False
            
    def display_bi_image_centered(self, bi_path, scale=1, color=Color.WHITE, bg_color=Color.BLACK):
        """
        在OLED显示屏中央显示BFile.bi格式的图片
        
        参数:
            bi_path: BFile.bi文件路径
            scale: 缩放比例，默认为1
            color: 图片颜色，默认为白色
            bg_color: 背景颜色，默认为黑色
            
        返回:
            bool: 是否成功显示
        """
        try:
            # 加载图片
            width, height, binary = self.load_bi_image(bi_path)
            if width is None or height is None or binary is None:
                print("Error: Failed to load image, cannot center display")
                return False
                
            # 计算居中位置
            x = (self.width - width * scale) // 2
            y = (self.height - height * scale) // 2
            
            # 显示图片
            return self.display_bi_image(bi_path, x, y, scale, color, bg_color)
            
        except Exception as e:
            print(f"Error: Failed to center display BFile.bi image: {str(e)}")
            return False
            
    def display_bi_animation(self, bi_paths, delay=0.1, scale=1, color=Color.WHITE, bg_color=Color.BLACK):
        """
        在OLED显示屏上显示BFile.bi格式的动画
        
        参数:
            bi_paths: BFile.bi文件路径列表
            delay: 帧间延迟，默认为0.1秒
            scale: 缩放比例，默认为1
            color: 图片颜色，默认为白色
            bg_color: 背景颜色，默认为黑色
            
        返回:
            bool: 是否成功显示
        """
        try:
            # 清屏
            self.oled.fill(bg_color)
            self.oled.show()
            
            # 显示每一帧
            for i, bi_path in enumerate(bi_paths):
                # 显示图片
                success = self.display_bi_image_centered(bi_path, scale, color, bg_color)
                if not success:
                    print(f"Error: Failed to display frame {i+1}")
                    return False
                    
                # 延迟
                time.sleep(delay)
                
            return True
            
        except Exception as e:
            print(f"Error: Failed to display BFile.bi animation: {str(e)}")
            return False 