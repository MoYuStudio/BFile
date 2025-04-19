"""
BRF Display Library for MicroPython
支持读取.bi和.bv文件并在LCD/OLED上显示
"""

import os
import framebuf

class BRFDisplay:
    def __init__(self, display=None):
        """
        初始化BRF显示类
        :param display: 显示器对象（支持framebuf的显示器）
        """
        self.display = display
        self.width = display.width if display else 0
        self.height = display.height if display else 0
        
    def read_bi_file(self, filename):
        """
        读取.bi文件
        :param filename: .bi文件路径
        :return: 图像数据
        """
        try:
            with open(filename, 'rb') as f:
                # 读取文件头
                width = int.from_bytes(f.read(2), 'little')
                height = int.from_bytes(f.read(2), 'little')
                # 读取图像数据
                data = bytearray(f.read())
                return width, height, data
        except OSError:
            print(f"无法打开文件: {filename}")
            return None, None, None
            
    def read_bv_file(self, filename):
        """
        读取.bv文件
        :param filename: .bv文件路径
        :return: 图像数据
        """
        try:
            with open(filename, 'rb') as f:
                # 读取文件头
                width = int.from_bytes(f.read(2), 'little')
                height = int.from_bytes(f.read(2), 'little')
                # 读取图像数据
                data = bytearray(f.read())
                return width, height, data
        except OSError:
            print(f"无法打开文件: {filename}")
            return None, None, None
            
    def show_bi(self, filename, x=0, y=0):
        """
        在显示器上显示.bi图像
        :param filename: .bi文件路径
        :param x: 显示位置的x坐标
        :param y: 显示位置的y坐标
        """
        if not self.display:
            print("未初始化显示器")
            return
            
        width, height, data = self.read_bi_file(filename)
        if data is None:
            return
            
        # 创建framebuffer
        fbuf = framebuf.FrameBuffer(data, width, height, framebuf.GS8)
        
        # 在显示器上显示图像
        self.display.blit(fbuf, x, y)
        self.display.show()
        
    def show_bv(self, filename, x=0, y=0):
        """
        在显示器上显示.bv图像
        :param filename: .bv文件路径
        :param x: 显示位置的x坐标
        :param y: 显示位置的y坐标
        """
        if not self.display:
            print("未初始化显示器")
            return
            
        width, height, data = self.read_bv_file(filename)
        if data is None:
            return
            
        # 创建framebuffer
        fbuf = framebuf.FrameBuffer(data, width, height, framebuf.GS8)
        
        # 在显示器上显示图像
        self.display.blit(fbuf, x, y)
        self.display.show()
        
    def clear(self):
        """
        清除显示器
        """
        if self.display:
            self.display.fill(0)
            self.display.show() 