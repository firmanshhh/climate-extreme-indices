"""
setup.py untuk instalasi development mode
Jalankan dari root project: pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="climate_extremes",
    version="1.0.0",
    description="ETCCDI Climate Extremes Indices Calculator for Tropical Regions",
    author="BMKG Climate Center",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "pytest>=7.0.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)