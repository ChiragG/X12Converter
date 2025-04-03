from setuptools import setup, find_packages

setup(
    name="json-to-edi837p",
    version="0.1.0",
    description="A Python library for converting JSON data to EDI 837P (Professional) format",
    author="Chiragg Helani",
    author_email="chiragghelani@gmail.com",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "python-dateutil>=2.8.2",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        "console_scripts": [
            "json-to-edi=json_to_edi:main",
        ],
    },
)

