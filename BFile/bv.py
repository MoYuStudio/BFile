#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BFile (Binary File) 视频模块
提供视频与BFile格式之间的转换功能
"""

import os
import cv2
import numpy as np
import struct
import shutil
import subprocess
from typing import Optional, Tuple, List

from .core import (
    encode_run_length, 
    decode_run_length, 
    compress_data, 
    decompress_data,
    get_file_size_info,
    Error,
    EncodeError,
    DecodeError,
    FileError
)


class Video:
    """视频处理类"""
    
    @staticmethod
    def mp4_to_bv(input_path: str, output_path: str, threshold: int = 128, target_fps: int = 10) -> bool:
        """
        将MP4视频转换为高度压缩的BV格式

        参数:
            input_path: 输入MP4视频路径
            output_path: 输出BV文件路径
            threshold: 二值化阈值，默认为128
            target_fps: 目标帧率，默认为10fps
            
        返回:
            是否成功
        """
        if not os.path.exists(input_path):
            raise FileError(f"输入文件不存在: {input_path}")
            
        if not input_path.lower().endswith(".mp4"):
            raise EncodeError("输入文件必须是MP4格式")

        try:
            # 打开视频文件
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                raise EncodeError("无法打开视频文件")

            # 获取视频信息
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # 计算帧间隔以匹配目标帧率
            frame_interval = int(fps / target_fps)
            if frame_interval < 1:
                frame_interval = 1

            with open(output_path, "wb") as f:
                # 写入视频信息头
                f.write(
                    struct.pack(
                        ">HHII", width, height, target_fps, total_frames // frame_interval
                    )
                )

                frame_count = 0
                processed_frames = 0
                
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
                        compressed_frame = compress_data(compressed_frame)
                        # 写入帧大小和帧数据
                        f.write(struct.pack(">I", len(compressed_frame)))
                        f.write(compressed_frame)
                        processed_frames += 1

                    frame_count += 1

            cap.release()
            
            # 打印转换信息
            input_size, output_size, compression_ratio = get_file_size_info(input_path, output_path)
            print(f"转换成功: {input_path} -> {output_path}")
            print(f"原始大小: {input_size} 字节")
            print(f"压缩后大小: {output_size} 字节")
            print(f"压缩率: {compression_ratio:.2f}%")
            print(f"处理帧数: {processed_frames}/{total_frames}")
            
            return True

        except Error:
            raise
        except Exception as e:
            raise EncodeError(f"MP4转BV失败: {str(e)}")

    @staticmethod
    def bv_to_mp4(input_path: str, output_path: str, fps: Optional[int] = None) -> bool:
        """
        将BV格式视频转换回MP4格式
        
        参数:
            input_path: 输入BV文件路径
            output_path: 输出MP4文件路径
            fps: 输出视频的帧率，如果为None则使用原始帧率
            
        返回:
            是否成功
        """
        if not os.path.exists(input_path):
            raise FileError(f"输入文件不存在: {input_path}")
            
        if not input_path.lower().endswith(".bv"):
            raise DecodeError("输入文件必须是BV格式")

        try:
            with open(input_path, "rb") as f:
                # 读取视频信息头
                width, height, target_fps, total_frames = struct.unpack(">HHII", f.read(12))
                
                # 如果未指定帧率，使用原始帧率
                if fps is None:
                    fps = target_fps

                # 创建临时目录存放帧图像
                temp_dir = "temp_frames"
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)

                # 读取并解码每一帧，保存为PNG图像
                for i in range(total_frames):
                    # 读取帧大小
                    frame_size = struct.unpack(">I", f.read(4))[0]
                    # 读取压缩的帧数据
                    compressed_frame = f.read(frame_size)
                    # 解压数据
                    decompressed_frame = decompress_data(compressed_frame)
                    # 解码帧数据
                    frame_data = decode_run_length(decompressed_frame, width * height)
                    # 重塑为图像
                    frame = frame_data.reshape(height, width) * 255
                    # 保存为PNG图像
                    frame_path = os.path.join(temp_dir, f"frame_{i:06d}.png")
                    cv2.imwrite(frame_path, frame)

                # 使用ffmpeg将PNG图像序列转换为MP4
                ffmpeg_path = os.path.join("depend", "ffmpeg.exe")
                if not os.path.exists(ffmpeg_path):
                    # 尝试在系统PATH中查找ffmpeg
                    ffmpeg_path = "ffmpeg"
                
                ffmpeg_cmd = [
                    ffmpeg_path,
                    "-framerate", str(fps),
                    "-i", os.path.join(temp_dir, "frame_%06d.png"),
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-y",
                    output_path
                ]
                
                print(f"执行FFmpeg命令: {' '.join(ffmpeg_cmd)}")
                
                # 使用subprocess代替os.system，提供更好的错误处理
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"FFmpeg错误: {result.stderr}")
                    raise DecodeError(f"FFmpeg转换失败: {result.stderr}")

                # 清理临时文件
                for i in range(total_frames):
                    frame_path = os.path.join(temp_dir, f"frame_{i:06d}.png")
                    if os.path.exists(frame_path):
                        os.remove(frame_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)

            print(f"转换成功: {input_path} -> {output_path}")
            return True

        except Error:
            raise
        except Exception as e:
            raise DecodeError(f"BV转MP4失败: {str(e)}")


def main():
    """主函数，用于测试"""
    try:
        # 测试MP4到BV的转换
        Video.mp4_to_bv("a_cut.mp4", "a_cut.bv", threshold=128, target_fps=10)
        
        # 测试BV到MP4的转换
        Video.bv_to_mp4("a_cut.bv", "a_cut_back.mp4")
        
    except Error as e:
        print(f"错误: {str(e)}")
    except Exception as e:
        print(f"未知错误: {str(e)}")


if __name__ == "__main__":
    main()