import setuptools
import os, sys

with open("README.md", "r") as fh:
    long_description = fh.read()

reqs = [i.strip() for i in open("requirements.txt").readlines()]
reqs = ["requests", "appdirs"]
if os.name == "nt" or sys.platform.lower().startswith("win"):
     reqs += ['windows-curses']
setuptools.setup(
    name="nodreader", # Replace with your own username
    version="0.1.2",
    author="A Pouramini",
    author_email="pouramini@gmail.com",
    description="Nodreader, a text-based article reader and manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/puraminy/nodreader",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'nodreader = nodreader.nodreader:main',
        ],
    },
    install_requires=reqs,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
