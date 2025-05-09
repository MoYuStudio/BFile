#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BFile Micro - 使用示例
展示如何使用BFile Micro模块显示图片和视频
包含OLED驱动初始化、图片显示和视频播放的完整示例
"""

import machine

import os
import time
import os
import sys


# 导入模块
from BFile_Micro import Color, BI, BV

def main():
    """
    主函数，演示BFile Micro模块的基本功能
    包括OLED驱动初始化、图片显示和视频播放
    """
    try:
        # 设置CPU频率为280MHz
        machine.freq(280_000_000)
        
        # 尝试导入OLED驱动
        oled = None
        
        # 尝试导入Pico OLED 1.5寸RGB驱动
        try:
            from drive.pico_oled_1in5_rgb import OLED_1inch5
            oled = OLED_1inch5()
        except ImportError:
            print("Error: Failed to import Pico OLED 1.5 inch RGB driver")
            
        # 如果无法导入OLED驱动，则退出
        if oled is None:
            print("Error: No OLED driver available, please ensure drive/pico_oled_1in5_rgb.py exists")
            return
            
        # 清屏
        oled.fill(Color.BLACK)
        oled.show()
        
        # 初始化BFileMicro
        BFile = BI(oled)
        
        # 检查BFile.bi文件是否存在
        try:
            with open("BFile.bi", "rb") as f:
                file_size = len(f.read())
        except OSError:
            print("Error: BFile.bi file not found")
            
        # 显示BFile.bi图片
        success = BFile.display_bi_image_centered("BFile.bi", scale=1, color=Color.WHITE)
        if not success:
            print("Error: Failed to display BFile.bi image")
            
        time.sleep(1)
        
        # 测试OLED是否工作 - 使用彩虹色序列以0.1秒刷新率显示
        print("Testing OLED with rainbow colors at 0.01s refresh rate...")
        for i in range(7):  # 彩虹色序列有7种颜色
            color = Color.RAINBOW[i]
            BFile.display_bi_image_centered("BFile.bi", scale=1, color=color)
            # time.sleep(0.1)
        
        # 初始化BFileVideoMicro
        BFile_video = BV(oled)
        
        # 检查BFile.bv文件是否存在
        try:
            with open("BFile.bv", "rb") as f:
                file_size = len(f.read())
        except OSError:
            print("Error: BFile.bv file not found")
            
        # 播放BFile.bv视频
        success = BFile_video.play_bv_video("BFile.bv", scale=1, color=Color.WHITE, loop=3)
        if not success:
            print("Error: Failed to play BFile.bv video")
            
        # 清屏
        oled.fill(Color.BLACK)
        oled.show()
        
    except Exception as e:
        print(f"Error: An error occurred while running the example: {str(e)}")
        
if __name__ == "__main__":
    main() 