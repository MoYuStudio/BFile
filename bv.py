#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import struct
import zlib
import os
from bi import encode_run_length, decode_run_length

def mp4_to_bv(input_path, output_path, threshold=128, target_fps=10):
    """
    将MP4视频转换为高度压缩的BV格式
    
    参数:
        input_path: 输入MP4视频路径
        output_path: 输出BV文件路径
        threshold: 二值化阈值，默认为128
        target_fps: 目标帧率，默认为10fps
    """
    if not input_path.lower().endswith('.mp4'):
        raise ValueError("输入文件必须是MP4格式")
    
    try:
        # 打开视频文件
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError("无法打开视频文件")
        
        # 获取视频信息
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 计算帧间隔以匹配目标帧率
        frame_interval = int(fps / target_fps)
        
        with open(output_path, 'wb') as f:
            # 写入视频信息头
            f.write(struct.pack('>HHII', width, height, target_fps, total_frames // frame_interval))
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 按目标帧率采样
                if frame_count % frame_interval == 0:
                    # 转换为灰度图
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    # 二值化处理
                    binary = (gray >= threshold).astype(np.uint8)
                    # 压缩帧数据
                    compressed_frame = encode_run_length(binary.flatten())
                    # 使用zlib进一步压缩
                    compressed_frame = zlib.compress(compressed_frame)
                    # 写入帧大小和帧数据
                    f.write(struct.pack('>I', len(compressed_frame)))
                    f.write(compressed_frame)
                
                frame_count += 1
        
        cap.release()
        print(f"转换成功: {input_path} -> {output_path}")
        print(f"原始大小: {os.path.getsize(input_path)} 字节")
        print(f"压缩后大小: {os.path.getsize(output_path)} 字节")
        print(f"压缩率: {(1 - os.path.getsize(output_path) / os.path.getsize(input_path)) * 100:.2f}%")
        return True
    
    except Exception as e:
        print(f"转换失败: {str(e)}")
        return False

def bv_to_mp4(input_path, output_path, fps=10):
    """
    将BV格式视频转换回MP4格式，使用ffmpeg.exe
    """
    if not input_path.lower().endswith('.bv'):
        raise ValueError("输入文件必须是BV格式")
    
    try:
        with open(input_path, 'rb') as f:
            # 读取视频信息头
            width, height, target_fps, total_frames = struct.unpack('>HHII', f.read(12))
            
            # 创建临时目录存放帧图像
            temp_dir = "temp_frames"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            # 读取并解码每一帧，保存为PNG图像
            for i in range(total_frames):
                # 读取帧大小
                frame_size = struct.unpack('>I', f.read(4))[0]
                # 读取压缩的帧数据
                compressed_frame = f.read(frame_size)
                # 解压数据
                decompressed_frame = zlib.decompress(compressed_frame)
                # 解码帧数据
                frame_data = decode_run_length(decompressed_frame, width * height)
                # 重塑为图像
                frame = frame_data.reshape(height, width) * 255
                # 保存为PNG图像
                frame_path = os.path.join(temp_dir, f"frame_{i:06d}.png")
                cv2.imwrite(frame_path, frame)
            
            # 使用ffmpeg将PNG图像序列转换为MP4
            ffmpeg_cmd = f'ffmpeg.exe -framerate {target_fps} -i "{temp_dir}/frame_%06d.png" -c:v libx264 -pix_fmt yuv420p -y "{output_path}"'
            print(f"执行FFmpeg命令: {ffmpeg_cmd}")
            os.system(ffmpeg_cmd)
            
            # 清理临时文件
            for i in range(total_frames):
                frame_path = os.path.join(temp_dir, f"frame_{i:06d}.png")
                if os.path.exists(frame_path):
                    os.remove(frame_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        
        print(f"转换成功: {input_path} -> {output_path}")
        return True
    
    except Exception as e:
        print(f"转换失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 测试MP4到BV的转换
    mp4_to_bv("a_cut.mp4", "a_cut.bv", threshold=128, target_fps=10)
    # 测试BV到MP4的转换
    bv_to_mp4("a_cut.bv", "a_cut_back.mp4")
