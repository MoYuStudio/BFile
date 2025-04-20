from setuptools import setup, find_packages

setup(
    name="b-file",
    version="0.1.0",
    description="BFile (Binary File) - 一个专为小型二值化图像开发优化的Python库",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="MoYuStudio",
    author_email="contact@moyustudio.com",
    url="https://github.com/MoYuStudio/BFile",
    packages=find_packages(),
    package_data={
        'BFile': ['*.py'],
        'BFile_Micro': ['*.py'],
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
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)