import BRF

# 测试PNG到BI的转换
BRF.Image.png_to_binary("assets/BRF.png", "generate/BRF.bi")

# 测试BI到PNG的转换
BRF.Image.binary_to_png("generate/BRF.bi", "generate/BRF_back.png")

# 测试MP4到BV的转换
BRF.Video.mp4_to_bv("assets/BRF.mp4", "generate/BRF.bv", target_fps=10)

# 测试BV到MP4的转换
BRF.Video.bv_to_mp4("generate/BRF.bv", "generate/BRF_back.mp4")

