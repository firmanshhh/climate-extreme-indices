"""
Minimal setup.py for local installation and development
No PyPI publishing required
"""

from setuptools import setup, find_packages

setup(
    name="climate-extremes",
    version="1.0.0",
    description="ETCCDI climate extremes indices calculator for tropical regions",
    author="BMKG Climate Center",
    author_email="climate.data@bmkg.go.id",
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.21.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "matplotlib>=3.5.0",
            "jupyter>=1.0.0",
        ],
    },
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