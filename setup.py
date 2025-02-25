from setuptools import setup, find_packages

setup(
    name="ai-companion",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "langchain>=0.1.0",
        "langchain-openai>=0.0.2",
        "langchain-community>=0.0.10",
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "qdrant-client>=1.6.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "tenacity>=8.2.0"
    ],
    python_requires=">=3.9",
) 