import os
from imp import load_source
from setuptools import setup, find_namespace_packages
from glob import glob
import io

name = "planetary-computer"
description = "Planetary Computer SDK for Python"

__version__ = load_source(
    "planetary_computer.version",
    os.path.join(os.path.dirname(__file__),
                 "planetary_computer/version.py")).__version__

here = os.path.abspath(os.path.dirname(__file__))

# get the dependencies and installs
with io.open(os.path.join(here, "requirements.txt"), encoding="utf-8") as f:
    install_requires = [line.split(" ")[0] for line in f.read().split("\n")]

    # TODO: Remove. Gets around error with git dependencies.
    install_requires = [x for x in install_requires if not x.startswith("git")]


with open(os.path.join(here, "README.md")) as readme_file:
    readme = readme_file.read()

setup(name=name,
      description=description,
      version=__version__,
      long_description=readme,
      long_description_content_type="text/markdown",
      author="microsoft",
      author_email="planetarycomputer@microsoft.com",
      packages=find_namespace_packages(),
      include_package_data=False,
      entry_points={"console_scripts": ["planetarycomputer=planetary_computer.scripts.cli:app"]},
      install_requires=install_requires)
