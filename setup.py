import codecs
import os
import re

from setuptools import setup, find_packages

# ------------------------------------------------------------------
#                         HELPER FUNCTIONS

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M, )
    if version_match:
        return version_match.group(1)

    raise RuntimeError("Unable to find version string.")


# ------------------------------------------------------------------
#                          POPULATE SETUP

setup(
    name="hyo2.kng",
    version=find_version("hyo2", "kng", "__init__.py"),
    license="LGPLv3 license",

    namespace_packages=[
        "hyo2"
    ],
    packages=find_packages(exclude=[
        "*.tests", "*.tests.*", "tests.*", "tests", "*.test*",
    ]),
    package_data={

    },
    zip_safe=False,
    ext_modules=None,
    setup_requires=[
        "setuptools",
        "wheel"
    ],
    install_requires=[
        "hyo2.abc",
    ],
    python_requires='>=3.5',
    entry_points={
        "gui_scripts": [
        ],
        "console_scripts": [
            "SIS4 = hyo2.kng.emu.sis4.__main__:main",
            "KCtrl = hyo2.kng.emu.kctrl.__main__:main",
        ],
    },
    test_suite="tests",

    description="Library and apps for Kongsberg Maritime data interaction.",
    long_description=read(os.path.join(here, "README.rst")),
    url="https://www.hydroffice.org/openbst/main",
    classifiers=[  # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    keywords="hydrography ocean mapping acoustic data format emulator",
    author="Giuseppe Masetti",
    author_email="gmasetti@ccom.unh.edu",
)
