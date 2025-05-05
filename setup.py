from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

with open("requirements.txt", "r") as f:
    install_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name = "sitm",
    version = "0.1.0",
    description = "Security-in-the-Middle (SiTM): Intercepting Vulnerabilities in Transit to Remote.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    author = "Chidera Biringa",
    author_email = "biringachidera@gmail.com",
    url = "https://github.com/biringaChi/sitm",
    license = "MPL-2.0",
    packages = find_packages(),
    python_requires = ">=3.8",
    install_requires = install_requires,
    entry_points = {
        "console_scripts": [
            "sitm = sitm_core.cli.sitm:main",
            "sitm-scan = sitm_core.cli.scan:sitm",
        ]
    },
    include_package_data = True,
    classifiers = [
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
