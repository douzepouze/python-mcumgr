import setuptools
import os

THIS_DIR = os.path.abspath(os.path.dirname(__file__))

VERSION = None
with open(os.path.join(THIS_DIR, "mcumgr", "__version__.py")) as f:
    tmp_dict = {}
    exec(f.read(), tmp_dict)
    VERSION = tmp_dict["__version__"]

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="douzepouze-python-mcumgr",
    version=VERSION,
    author="Steffen Görtz, Lohmega",
    author_email="steffen.goertz@grandcentrix.net",
    entry_points={"console_scripts": ["pymcumgr=mcumgr.cli:main"]},
    description="Library and command line tool for mcumgr protocol(s)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/douzepouze/python-mcumgr",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "cbor",
        "asyncclick",
        "anyio",
        "bleak > 0.5.1",
    ],
    python_requires='>=3.4',
)
