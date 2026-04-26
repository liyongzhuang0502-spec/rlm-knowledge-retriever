from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="rlm-knowledge-retriever",
    version="1.0.0",
    author="RLM Knowledge Retriever Contributors",
    description="Recursive Language Model based knowledge base retrieval for AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rlm-knowledge-retriever",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "rlms>=0.1.0",
        "openai>=1.0.0",
    ],
    extras_require={
        "semantic": ["sentence-transformers>=2.0.0", "numpy>=1.24.0"],
        "dev": ["pytest>=7.0.0", "black>=23.0.0", "mypy>=1.0.0"],
        "all": [
            "sentence-transformers>=2.0.0",
            "numpy>=1.24.0",
            "anthropic>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "rlm-kb=rlm_kb.rlm_kb:main",
        ]
    },
    keywords="rlm recursive-language-model knowledge-base retrieval rag agent ai",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/rlm-knowledge-retriever/issues",
        "Source": "https://github.com/yourusername/rlm-knowledge-retriever",
    },
)
