#!/usr/bin/env python3
"""
Setup script for NEYROLOCK - AI Desktop Application with Telegram Bot
"""

from setuptools import setup, find_packages
from pathlib import Path

readme_file = Path(__file__).parent / "PROJECT_DOCUMENTATION.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="neyrolock",
    version="3.0.0",
    description="NEYROLOCK - Local AI Models Desktop Application with Telegram Bot Integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="NEYROLOCK Team",
    author_email="team@neyrolock.ai",
    url="https://github.com/neyrolock/neyrolock",

    # Package configuration
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    py_modules=[
        "ai_gui_v3",
        "telegram_bot",
        "model_manager",
        "sync_manager",
        "ai_cli",
        "universal_cli",
        "lmstudio_cli",
        "local_model_cli",
    ],

    python_requires=">=3.10",

    # Dependencies - base installation
    install_requires=[
        "rich>=13.0.0",
        "huggingface-hub>=0.20.0",
        "requests>=2.31.0",
    ],

    # Optional dependencies for different features
    extras_require={
        # Full GUI application
        "gui": [
            "llama-cpp-python>=0.2.0",
            "Pillow>=10.0.0",
            "tkhtmlview>=0.2.0",
        ],

        # Telegram bot
        "telegram": [
            "python-telegram-bot>=20.0",
            "llama-cpp-python>=0.2.0",
        ],

        # LM Studio support
        "lmstudio": [
            "lmstudio>=1.5.0",
        ],

        # Cloud APIs support (Groq, OpenAI, Ollama)
        "cloud": [
            "openai>=1.0.0",
        ],

        # Development tools
        "dev": [
            "pyinstaller>=6.0.0",
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],

        # Complete installation (all features)
        "all": [
            "llama-cpp-python>=0.2.0",
            "python-telegram-bot>=20.0",
            "lmstudio>=1.5.0",
            "openai>=1.0.0",
            "Pillow>=10.0.0",
            "tkhtmlview>=0.2.0",
        ],
    },

    # Entry points for command-line scripts
    entry_points={
        "console_scripts": [
            "neyrolock-gui=ai_gui_v3:main",
            "neyrolock-cli=ai_cli:main",
            "neyrolock-bot=telegram_bot:main",
            "neyrolock-universal=universal_cli:main",
            "neyrolock-lmstudio=lmstudio_cli:main",
        ],
    },

    # Include additional files
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json"],
    },

    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Communications :: Chat",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
    ],

    keywords="ai llm chatbot telegram gui local-models llama huggingface",

    project_urls={
        "Bug Reports": "https://github.com/neyrolock/neyrolock/issues",
        "Documentation": "https://github.com/neyrolock/neyrolock/blob/main/PROJECT_DOCUMENTATION.md",
        "Source": "https://github.com/neyrolock/neyrolock",
    },
)
