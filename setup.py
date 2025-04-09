from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="needle-track",
    version="0.1.4",
    author="Xinyue Sheng",
    author_email="XinyueSheng@outlook.com",
    description="Transient Recognition, Annotation, and Classification Kit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/XinyueSheng2019/NEEDLE-TRACK",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    entry_points={
        'console_scripts': [
            'needle-track=needle_track.__main__:main',
        ],
    },
    install_requires=[
        'numpy',
        'pandas',
        'astropy'
        # Add other dependencies, see environment.yml
    ],
) 