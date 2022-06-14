"""Build CRISPRme"""

from importlib_metadata import entry_points
from setuptools import setup, find_packages, Extension
from distutils.version import LooseVersion
from distutils.command.sdist import sdist 
from distutils.command.build_ext import build_ext 

import sys

try:  # sphinx could not be available
    from sphinx.setup_command import BuildDoc
except ImportError:
    sys.stderr.write("\nSphinx package is required to install CRISPRme.\n")
    sys.exit(1)


# check python version --> Python >= 3.6 required
if sys.version_info[:2] < (3,6):
    sys.stderr.write("\nCRISPRme requires Python >= 3.6\n")  
    sys.exit(1)
# parse README file
encoding_dict = {"encoding": "utf-8"} if sys.version_info[0] >= 3 else dict()
readmefile = "README.md"
with open(readmefile, **encoding_dict) as handle:
    long_description = handle.read()
# package name
name = "CRISPRme"
version = "2.1.0"
# define setup()
setup(
    name="crisprme",
    version=version,
    author="Samuele Cancellieri, Manuel Tognon",
    author_email="manu.tognon@gmail.com",
    url="https://github.com/pinellolab/CRISPRme",
    description="CRISPRme is a web based tool dedicated to perform predictive "
                "analysis and result assessement on CRISPR/Cas experiments with "
                "a user-friendly GUI and the precise scope of searching "
                "individual variant in VCF dateset.",
    long_description=long_description,
    license="AGPL-3.0",
    cmdclass={"build_sphinx": BuildDoc},
    command_options={
        "build_sphinx": {
            "project": ("setup.py", name),
            "version": ("setup.py", version),
            "source_dir": ("setup.py", "docs")
        }
    },
    packages=find_packages("src"),
    package_dir={"": "src"},
    entry_points={"console_scripts": ["crisprme = crisprme.__main__:main"]},
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: AGPL-3.0 License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Bio-Informatics"
    ],
)

