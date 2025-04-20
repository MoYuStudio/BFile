#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BFile Micro - BFile视频显示模块
用于在PicoPi的OLED显示屏上显示BFile.bv格式的视频
支持视频加载、播放、暂停、恢复和停止等功能
"""

import struct
import time
import os
from machine import Pin, SPI
import framebuf
import sys
import gc

from BFile_Micro.color import Color

class BV:
    """BFile视频显示类，用于在OLED显示屏上显示BFile.bv格式的视频"""
    
    def __init__(self, oled_display):
        """
        初始化BFile视频显示类
        
        参数:
            oled_display: OLED显示对象，必须是framebuf.FrameBuffer的子类
        """
        self.oled = oled_display
        self.width = oled_display.width
        self.height = oled_display.height
        self.paused = False
        self.playing = False
        self.frame_cache = {}  # 帧缓存
        self.max_cache_size = 10  # 最大缓存帧数
        self.auto_update = True  # 自动更新显示
        
        # 如果OLED对象有set_auto_update方法，则设置自动更新
        if hasattr(self.oled, 'set_auto_update'):
            self.oled.set_auto_update(False)  # 关闭自动更新，提高性能
        
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
            
        # 使用bytearray代替list，提高性能
        result = bytearray(total_bits)
        pos = 0
        current = data[0]
        
        # 从第二个字节开始解码
        for i in range(1, len(data)):
            packed = data[i]
            count = (packed >> 4) & 0xF  # 获取高4位的计数
            current = packed & 0xF  # 获取低4位的当前位值
            
            # 批量填充，而不是逐个添加
            for j in range(count):
                if pos < total_bits:
                    result[pos] = current
                    pos += 1
                else:
                    break
                    
        # 如果长度不够，用最后一个位填充
        while pos < total_bits:
            result[pos] = current
            pos += 1
            
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
                # 使用extend代替循环，提高性能
                if start >= 0 and start + length <= len(result):
                    result.extend(result[start:start+length])
                else:
                    # 处理边界情况
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
        
    def load_bv_frame(self, bv_file, frame_index):
        """
        从BV文件中加载指定帧
        
        参数:
            bv_file: 已打开的BV文件对象
            frame_index: 帧索引
            
        返回:
            (width, height, binary_data): 帧宽度、高度和二值化数据
        """
        # 检查缓存中是否已有该帧
        if frame_index in self.frame_cache:
            return self.video_width, self.video_height, self.frame_cache[frame_index]
            
        try:
            # 读取帧大小
            frame_size_bytes = bv_file.read(4)
            if len(frame_size_bytes) < 4:
                print(f"Error: Cannot read frame size, file may have ended")
                return None, None, None
                
            frame_size = struct.unpack(">I", frame_size_bytes)[0]
            
            # 读取压缩的帧数据
            compressed_frame = bv_file.read(frame_size)
            if len(compressed_frame) < frame_size:
                print(f"Error: Incomplete frame data: {len(compressed_frame)}/{frame_size} bytes")
                return None, None, None
                
            # 解压数据
            encoded = self.decompress_data(compressed_frame)
            
            # 计算总位数
            total_bits = self.video_width * self.video_height
            
            # 解码游程长度
            binary = self.decode_run_length(encoded, total_bits)
            
            # 缓存帧数据
            if len(self.frame_cache) >= self.max_cache_size:
                # 如果缓存已满，删除最早的帧
                oldest_frame = min(self.frame_cache.keys())
                del self.frame_cache[oldest_frame]
                
            self.frame_cache[frame_index] = binary
            
            return self.video_width, self.video_height, binary
            
        except Exception as e:
            print(f"Error: Failed to load BV frame: {str(e)}")
            return None, None, None
            
    def load_bv_video(self, bv_path):
        """
        加载BFile.bv格式的视频
        
        参数:
            bv_path: BFile.bv文件路径
            
        返回:
            bool: 是否成功加载
        """
        try:
            # 清空帧缓存
            self.frame_cache.clear()
            
            # 检查文件是否存在
            try:
                with open(bv_path, "rb") as f:
                    # 读取视频信息头
                    header = f.read(12)
                    if len(header) < 12:
                        print(f"Error: Incomplete file header: {len(header)} bytes")
                        return False
                        
                    self.video_width, self.video_height, self.fps, self.total_frames = struct.unpack(">HHII", header)
                    
                    # 保存文件路径和帧数信息
                    self.bv_path = bv_path
                    self.current_frame = 0
                    
                    return True
            except OSError:
                print(f"Error: File not found: {bv_path}")
                return False
                
        except Exception as e:
            print(f"Error: Failed to load BFile.bv video: {str(e)}")
            return False
            
    def display_bv_frame(self, width, height, binary, x=0, y=0, scale=1, color=Color.WHITE, bg_color=Color.BLACK):
        """
        在OLED显示屏上显示BV帧
        
        参数:
            width: 帧宽度
            height: 帧高度
            binary: 二值化数据
            x: 显示位置的x坐标
            y: 显示位置的y坐标
            scale: 缩放比例，默认为1
            color: 图片颜色，默认为白色
            bg_color: 背景颜色，默认为黑色
            
        返回:
            bool: 是否成功显示
        """
        try:
            # 检查帧尺寸是否超过屏幕
            if width * scale > self.width or height * scale > self.height:
                print(f"Error: Frame size ({width}x{height}) is too large to display")
                return False
                
            # 清屏
            self.oled.fill(bg_color)
            
            # 优化：直接使用framebuf的方法绘制，而不是创建像素列表
            if scale == 1:
                # 如果不需要缩放，直接绘制
                for i in range(height):
                    for j in range(width):
                        pixel = binary[i * width + j]
                        if pixel == 1:
                            self.oled.pixel(x + j, y + i, color)
                        elif bg_color != Color.BLACK:
                            self.oled.pixel(x + j, y + i, bg_color)
            else:
                # 如果需要缩放，使用优化的方法
                for i in range(height):
                    for j in range(width):
                        pixel = binary[i * width + j]
                        if pixel == 1:
                            # 使用fill_rect代替多个pixel调用，提高性能
                            self.oled.fill_rect(x + j * scale, y + i * scale, scale, scale, color)
                        elif bg_color != Color.BLACK:
                            self.oled.fill_rect(x + j * scale, y + i * scale, scale, scale, bg_color)
            
            # 更新显示
            if self.auto_update:
                self.oled.show()
                
            return True
            
        except Exception as e:
            print(f"Error: Failed to display BV frame: {str(e)}")
            return False
            
    def display_bv_frame_centered(self, width, height, binary, scale=1, color=Color.WHITE, bg_color=Color.BLACK):
        """
        在OLED显示屏中央显示BV帧
        
        参数:
            width: 帧宽度
            height: 帧高度
            binary: 二值化数据
            scale: 缩放比例，默认为1
            color: 图片颜色，默认为白色
            bg_color: 背景颜色，默认为黑色
            
        返回:
            bool: 是否成功显示
        """
        try:
            # 计算居中位置
            x = (self.width - width * scale) // 2
            y = (self.height - height * scale) // 2
            
            # 显示帧
            return self.display_bv_frame(width, height, binary, x, y, scale, color, bg_color)
            
        except Exception as e:
            print(f"Error: Failed to center display BV frame: {str(e)}")
            return False
            
    def play_bv_video(self, bv_path, scale=1, color=Color.WHITE, bg_color=Color.BLACK, loop=1):
        """
        播放BFile.bv格式的视频
        
        参数:
            bv_path: BFile.bv文件路径
            scale: 缩放比例，默认为1
            color: 图片颜色，默认为白色
            bg_color: 背景颜色，默认为黑色
            loop: 循环次数，默认为1（播放一次），0表示不播放，2、3、4等表示循环相应次数，-1表示无限循环
            
        返回:
            bool: 是否成功播放
        """
        try:
            # 加载视频
            if not self.load_bv_video(bv_path):
                print("Error: Failed to load video, cannot play")
                return False
                
            # 计算帧延迟时间
            frame_delay = 1.0 / self.fps
            
            # 关闭自动更新，提高性能
            if hasattr(self.oled, 'set_auto_update'):
                self.oled.set_auto_update(False)
                
            # 使用更简单、更直接的循环逻辑
            for i in range(loop):
                # 打开视频文件
                with open(bv_path, "rb") as f:
                    # 跳过文件头
                    f.read(12)
                    
                    # 播放每一帧
                    for i in range(self.total_frames):
                        # 加载帧
                        width, height, binary = self.load_bv_frame(f, i)
                        if width is None or height is None or binary is None:
                            print(f"Error: Failed to load frame {i+1}")
                            return False
                            
                        # 显示帧
                        success = self.display_bv_frame_centered(width, height, binary, scale, color, bg_color)
                        if not success:
                            print(f"Error: Failed to display frame {i+1}")
                            return False
                            
                        # 手动更新显示
                        self.oled.show()
                        
                        # 延迟
                        time.sleep(frame_delay)
                        
                        # 定期进行垃圾回收，防止内存泄漏
                        if i % 10 == 0:
                            gc.collect()
                    
            # 恢复自动更新
            if hasattr(self.oled, 'set_auto_update'):
                self.oled.set_auto_update(True)
                
            return True
            
        except Exception as e:
            print(f"Error: Failed to play BFile.bv video: {str(e)}")
            # 确保恢复自动更新
            if hasattr(self.oled, 'set_auto_update'):
                self.oled.set_auto_update(True)
            return False
            
    def play_bv_video_with_controls(self, bv_path, scale=1, color=Color.WHITE, bg_color=Color.BLACK):
        """
        播放BFile.bv格式的视频，支持控制
        
        参数:
            bv_path: BFile.bv文件路径
            scale: 缩放比例，默认为1
            color: 图片颜色，默认为白色
            bg_color: 背景颜色，默认为黑色
            
        返回:
            bool: 是否成功播放
        """
        try:
            # 加载视频
            if not self.load_bv_video(bv_path):
                print("Error: Failed to load video, cannot play")
                return False
                
            # 计算帧延迟时间
            frame_delay = 1.0 / self.fps
            
            # 关闭自动更新，提高性能
            if hasattr(self.oled, 'set_auto_update'):
                self.oled.set_auto_update(False)
                
            # 播放视频
            self.playing = True
            self.paused = False
            
            # 打开视频文件
            with open(bv_path, "rb") as f:
                # 跳过文件头
                f.read(12)
                
                # 播放每一帧
                for i in range(self.total_frames):
                    # 检查是否暂停
                    while self.paused:
                        time.sleep(0.1)
                        
                    # 检查是否停止
                    if not self.playing:
                        break
                        
                    # 加载帧
                    width, height, binary = self.load_bv_frame(f, i)
                    if width is None or height is None or binary is None:
                        print(f"Error: Failed to load frame {i+1}")
                        return False
                        
                    # 显示帧
                    success = self.display_bv_frame_centered(width, height, binary, scale, color, bg_color)
                    if not success:
                        print(f"Error: Failed to display frame {i+1}")
                        return False
                        
                    # 手动更新显示
                    self.oled.show()
                        
                    # 延迟
                    time.sleep(frame_delay)
                    
                    # 定期进行垃圾回收，防止内存泄漏
                    if i % 10 == 0:
                        gc.collect()
                    
            # 恢复自动更新
            if hasattr(self.oled, 'set_auto_update'):
                self.oled.set_auto_update(True)
                
            return True
            
        except Exception as e:
            print(f"Error: Failed to play BFile.bv video: {str(e)}")
            # 确保恢复自动更新
            if hasattr(self.oled, 'set_auto_update'):
                self.oled.set_auto_update(True)
            return False
            
    def pause_video(self):
        """
        暂停视频播放
        """
        self.paused = True
        
    def resume_video(self):
        """
        恢复视频播放
        """
        self.paused = False
        
    def stop_video(self):
        """
        停止视频播放
        """
        self.playing = False 