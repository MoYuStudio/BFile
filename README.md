# BRF (Binary Run-length File) 格式

BRF是一种专为低功耗设备（如单片机、嵌入式系统）设计的高效文件格式，专为二值化数据（如黑白图像和视频）优化，采用改进的游程编码算法进行压缩。相比传统PBM格式，BRF能够实现约70%的压缩率，同时保持接近的解码性能。

## 格式特点

- **二值化处理 (Binary)**: 将输入数据转换为二值（0和1）表示
- **游程编码 (Run-length)**: 使用改进的游程编码算法进行数据压缩
- **通用文件格式 (File)**: 支持多种媒体类型，包括图像和视频
- **低功耗优化**: 专为资源受限设备设计，最小化内存占用和CPU使用

## 技术优势

1. **高效压缩**:

   - 相比PBM格式减少约70%的文件体积
   - 优化的游程编码算法，减少冗余数据
   - 支持可变长度编码，适应不同数据特征
2. **低资源消耗**:

   - 最小化内存占用（通常<1KB RAM）
   - 低CPU使用率，适合电池供电设备
   - 无需复杂的数据结构支持
3. **快速解码**:

   - 接近PBM格式的解码速度
   - 简单的解码算法，易于实现
   - 支持流式处理，无需完整加载文件
4. **通用性**:

   - 支持多种媒体类型，不局限于特定格式
   - 兼容主流MCU平台
   - 易于移植到不同硬件环境

## 使用场景

- 单片机图像存储
- 嵌入式系统日志
- 低功耗传感器数据
- 工业控制面板显示
- 电子墨水屏显示
- 简单图形界面存储

## 性能对比

| 特性       | BRF   | PBM  |
| ---------- | ----- | ---- |
| 文件大小   | ~30%  | 100% |
| 解码速度   | ~100% | 100% |
| RAM占用    | <1KB  | ~3KB |
| CPU使用    | 低    | 中   |
| 实现复杂度 | 简单  | 简单 |

## 文件格式规范

### 文件头

```
BRF\x01    // 魔数
version    // 版本号（1字节）
width      // 宽度（4字节）
height     // 高度（4字节）
type       // 数据类型（1字节：0=图像，1=视频）
flags      // 标志位（1字节：压缩选项等）
```

### 数据块

```
length     // 游程长度（变长编码）
value      // 二值（0或1）
```

## 开发计划

- [ ] 基础格式实现
- [ ] 单片机示例代码
- [ ] 压缩算法优化
- [ ] 工具链开发
- [ ] 性能基准测试

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进BRF格式。请确保：

1. 遵循现有的代码风格
2. 添加适当的测试用例
3. 更新相关文档
4. 提供性能测试数据

## 许可证

Apache License 2.0

Copyright 2024 BRF Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
