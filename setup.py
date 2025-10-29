"""Setup configuration for the pricing agent package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of requirements.txt
requirements_path = Path(__file__).parent / "requirements.txt"
with open(requirements_path, 'r', encoding='utf-8') as f:
    requirements = [
        line.strip() 
        for line in f 
        if line.strip() and not line.startswith('#') and not line.startswith('-e')
    ]

readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name="pricing-agent",
    version="0.1.0",
    description="A Python package for analyzing dark web pricing documents and estimating data breach pricing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SG4083",
    python_requires=">=3.7",
    packages=find_packages(exclude=["tests", "tests.*", "venv", "venv.*"]),
    py_modules=["gpt_invoker"],  # Include gpt_invoker.py from root
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'pricing-agent=pricing_agent.cli:cli',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    include_package_data=True,
    zip_safe=False,
)

