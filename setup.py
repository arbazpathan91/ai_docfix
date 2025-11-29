from setuptools import setup, find_packages

setup(
    name="ai-docfix",
    version="0.1.0",  # Bumped version for the new architecture
    description="Automatically generate docstrings using LiteLLM (Vertex AI, OpenAI, Local, etc.)",
    author="Arbaz Pathan",
    packages=find_packages(),
    python_requires=">=3.9",  # LiteLLM generally prefers newer Python
    install_requires=[
        "litellm>=1.35.0",           # The core logic
    ],
    # This tells Python to treat the 'ai-docfix' file in your root folder as an executable
    scripts=[
        "ai-docfix",
    ],
)