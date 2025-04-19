from setuptools import setup, find_packages

setup(
    name="brf",
    version="0.1.0",
    description="BRF (Binary Run-length File) - 一个用于处理二值化图像和视频的Python库",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    package_data={
        'BRF': ['*.py'],
    },
    include_package_data=True,
    install_requires=[
        "numpy>=1.19.0",
        "Pillow>=8.0.0",
        "opencv-python>=4.5.0",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)