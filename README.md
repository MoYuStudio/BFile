<div align="center">
  <img src="assets/BRFx10.png" alt="BRF Logo" width="200"/>
</div>

# BRF (Binary Run-length File) 二值化游程文件

BRF是一个专为小型二值化图像开发优化的Python库。它提供了一种高效的压缩格式，特别适合存储和处理二值化的图像和视频数据。

## 项目简介

BRF库采用改进过后的游程编码算法，专为小型二值化图像和视频优化设计，能够实现极高的压缩率。该库最初在资源受限的树莓派Pico Pi 2上开发并优化，其有限的计算资源使其成为测试和验证BRF压缩算法的理想平台。BRF支持多种格式转换，包括PNG到BRF、MP4到BV等，并提供base64编码支持，便于网络传输。由于其极高的压缩率和快速的解码速度，BRF特别适合在资源受限的环境中使用，如嵌入式设备、移动应用或需要快速加载的Web应用。在遮罩图层和开发图层等只需要黑白二值信息的场景中，BRF格式可以显著减少存储空间和传输带宽，提高应用性能。

## 文件格式对比

### BRF.BI图像格式对比与其他格式对比

**以下为BRF库中的示例图像文件 (128x128像素的BRF Logo)**

| 特性              | BI               | PNG                | PBM                | JPG                | BMP                |
| ----------------- | ---------------- | ------------------ | ------------------ | ------------------ | ------------------ |
| 文件大小(128x128) | 110 B            | 373 B              | 521 B              | 2,943 B            | 16,454 B           |
| 压缩率(对比BMP)   | 99.3%            | 97.7%              | 96.8%              | 82.1%              | 基准               |
| 压缩类型          | 无损             | 无损               | 无损               | 有损               | 无损               |
| 解码速度          | 极快             | 慢                 | 快                 | 慢                 | 快                 |
| 色彩支持          | 仅黑白           | 全彩               | 仅黑白             | 全彩               | 全彩               |
| 透明度            | 不支持           | 支持               | 不支持             | 不支持             | 不支持             |
| 兼容性            | 需要BRF库        | 广泛               | 广泛               | 广泛               | 广泛               |
| 示例文件下载      | [BI](assets/BRF.bi) | [PNG](assets/BRF.png) | [PBM](assets/BRF.pbm) | [JPG](assets/BRF.jpg) | [BMP](assets/BRF.bmp) |

### BRF.BV视频格式对比与其他格式对比

**以下为BRF库中的示例视频文件 (128x128像素，8fps的BRF Logo动画)**

| 特性                   | BV               | GIF                | MP4                | MOV      | AVI      |
| ---------------------- | ---------------- | ------------------ | ------------------ | -------- | -------- |
| 文件大小(128x128 8fps) | 465 B            | 1,863 B            | 31,286 B           | 32,768 B | 65,536 B |
| 压缩率(对比AVI)        | 99.3%            | 97.2%              | 52.3%              | 50.0%    | 基准     |
| 压缩类型               | 无损             | 无损               | 有损               | 有损     | 无损     |
| 解码速度               | 极快             | 快                 | 慢                 | 慢       | 快       |
| 色彩支持               | 仅黑白           | 256色              | 全彩               | 全彩     | 全彩     |
| 音频支持               | 不支持           | 不支持             | 支持               | 支持     | 支持     |
| 兼容性                 | 需要BRF库        | 广泛               | 广泛               | 广泛     | 广泛     |
| 示例文件下载           | [BV](assets/BRF.bv) | [GIF](assets/BRF.gif) | [MP4](assets/BRF.mp4) | 暂无     | 暂无     |

## 本地安装

由于这是一个本地库，您需要将代码克隆到本地并安装：

```bash
# 克隆仓库
git clone https://github.com/MoYuStudio/BRF.git

# 进入项目目录
cd BRF

# 安装依赖
pip install -r requirements.txt

# 安装库
pip install -e .
```

## 特性

- 支持PNG图像与BRF格式之间的转换
- 支持MP4视频与BV格式之间的转换
- 使用改进的游程编码算法进行数据压缩
- 支持base64编码转换
- 提供详细的压缩率信息
- 支持自定义二值化阈值
- 支持视频帧率调整

## 使用方法

### 图像处理

```python
import BRF

# PNG转BRF
BRF.Image.png_to_binary("input.png", "output.bi", threshold=128)

# BRF转PNG
BRF.Image.binary_to_png("input.bi", "output.png")

# BRF转base64
base64_data = BRF.Image.bi_to_base64("input.bi")

# base64转BRF
BRF.Image.base64_to_bi(base64_data, "output.bi")

# 获取压缩信息
info = BRF.Image.get_compression_info("input.bi")
print(f"原始大小: {info['original_size']} 字节")
print(f"压缩后大小: {info['compressed_size']} 字节")
print(f"压缩率: {info['compression_ratio']:.2f}%")
```

### 视频处理

```python
import BRF

# MP4转BV
BRF.Video.mp4_to_bv("input.mp4", "output.bv", threshold=128, target_fps=10)

# BV转MP4
BRF.Video.bv_to_mp4("input.bv", "output.mp4")

# 获取视频信息
info = BRF.Video.get_video_info("input.bv")
print(f"帧数: {info['frame_count']}")
print(f"分辨率: {info['width']}x{info['height']}")
print(f"帧率: {info['fps']}")
```

## API文档

### BRF.Image

- `png_to_binary(png_path, bi_path, threshold=128)`: 将PNG图像转换为BRF格式
- `binary_to_png(bi_path, png_path)`: 将BRF格式转换为PNG图像
- `bi_to_base64(bi_path)`: 将BRF文件转换为base64字符串
- `base64_to_bi(base64_str, bi_path)`: 将base64字符串转换为BRF文件
- `get_compression_info(bi_path)`: 获取BRF文件的压缩信息

### BRF.Video

- `mp4_to_bv(mp4_path, bv_path, threshold=128, target_fps=10)`: 将MP4视频转换为BV格式
- `bv_to_mp4(bv_path, mp4_path)`: 将BV格式转换为MP4视频
- `get_video_info(bv_path)`: 获取BV文件的视频信息

## 依赖

- numpy >= 1.19.0
- Pillow >= 8.0.0
- opencv-python >= 4.5.0

## 项目结构

```
BRF/
├── BRF/
│   ├── __init__.py
│   ├── bi.py          # 图像处理模块
│   ├── bv.py          # 视频处理模块
│   └── core.py        # 核心功能模块
├── tests/              # 测试用例
├── examples/           # 示例代码
├── setup.py            # 安装配置
├── requirements.txt    # 依赖列表
└── README.md           # 本文档
```

## 许可证

Apache 许可证 2.0

&copy; 2025 MoYuStudio. All rights reserved.

根据Apache许可证2.0版（"许可证"）授权；
除非符合许可证，否则不得使用此文件。
您可以在以下位置获取许可证副本：

    http://www.apache.org/licenses/LICENSE-2.0

除非适用法律要求或书面同意，否则根据许可证分发的软件是基于
"按原样"提供的，没有任何明示或暗示的保证或条件。
有关许可证下的特定语言管理权限和
限制，请参阅许可证。
