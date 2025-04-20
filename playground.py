import BFile

# 测试PNG到BI的转换
BFile.Image.png_to_binary("assets/BFile.png", "generate/BFile.bi")

# 测试BI到PNG的转换
BFile.Image.binary_to_png("generate/BFile.bi", "generate/BFile_back.png")

# 测试MP4到BV的转换
BFile.Video.mp4_to_bv("assets/BFile.mp4", "generate/BFile.bv", target_fps=10)

# 测试BV到MP4的转换
BFile.Video.bv_to_mp4("generate/BFile.bv", "generate/BFile_back.mp4")

