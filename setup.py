# setup.py
from setuptools import setup, find_packages





with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name = "godart",
    version = "1.0.0",
    author = "rodolfocasan",
    author_email = "contact.christcastr@gmail.com",
    description = "Sistema de IA con manejo inteligente",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/rodolfocasan/godart",
    packages = find_packages(),
    classifiers = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires = ">=3.10",
    install_requires = [
        "supabase==2.27.2",
        "google-genai==1.60.0",
    ],
    include_package_data = True,
)