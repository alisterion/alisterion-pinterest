#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name="alisterion-pinterest",
      version="0.0.1",
      description="Pinterest API client",
      license="MIT",
      install_requires=["requests==2.9.1"],
      author="Alisterion",
      author_email="api@pinterest.com",
      url="",
      packages=find_packages(),
      keywords="pinterest",
      zip_safe=True)
