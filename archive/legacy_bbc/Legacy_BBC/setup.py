#!/usr/bin/env python3
"""
BBC (Bitter Brain Context) v8.6 Setup Script
Installation: pip install .
"""

from setuptools import setup, find_packages
import os

# Read README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="bbc-master",
    version="8.6.0",
    author="BBC Development Team",
    author_email="",
    description="Bitter Brain Context - local AI coding context and verification layer",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Anubis44197/BBC_MASTER_BBCMath",
    packages=find_packages(),
    py_modules=["bbc", "run_bbc", "bbc_daemon", "bbc_installer"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Editors :: Integrated Development Environments (IDE)",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "bbc=bbc:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai assistant context ide development tools",
    project_urls={
        "Bug Reports": "https://github.com/Anubis44197/BBC_MASTER_BBCMath/issues",
        "Source": "https://github.com/Anubis44197/BBC_MASTER_BBCMath",
        "Documentation": "https://github.com/Anubis44197/BBC_MASTER_BBCMath#readme",
    },
)
