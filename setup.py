from setuptools import setup, find_packages

setup(
    name="ai-docfix",
    version="0.1.0",
    description="Automatically generate docstrings for undocumented functions using Google's Gemini API",
    author="Arbaz Pathan",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "google-generativeai",
    ],
    scripts=[
        "ai-docfix",
    ],
)