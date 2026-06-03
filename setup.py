from setuptools import setup, find_packages

setup(
    name="automated-report-system",
    version="1.0.0",
    description="Automated weekly business report generation from raw database exports",
    author="Your Name",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "openpyxl>=3.1.2",
        "requests>=2.31.0",
        "schedule>=1.2.0",
        "numpy>=1.24.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": ["pytest>=7.4.0", "pytest-cov>=4.1.0"],
    },
    entry_points={
        "console_scripts": [
            "generate-report=main:main",
        ],
    },
)
