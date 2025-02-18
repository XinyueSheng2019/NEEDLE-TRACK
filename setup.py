from setuptools import setup, find_packages

setup(
    name="needle-track",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Add your dependencies here
    ],
    entry_points={
        'console_scripts': [
            'needle-track=needle_track.__main__:main',
        ],
    },
    author="Xinyue Sheng",
    author_email="XinyueSheng@outlook.com",
    description="Transient Recognition, Annotation, and Classification Kit",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/XinyueSheng2019/NEEDLE-TRACK",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
) 