"""
Setup script for hashcards
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hashcards",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Local-first spaced repetition learning with Markdown",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/1998x-stack/hashcards",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "flask>=2.3.0",
    ],
    entry_points={
        "console_scripts": [
            "hashcards=hashcards.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "hashcards": [
            "web/templates/*.html",
        ],
    },
)