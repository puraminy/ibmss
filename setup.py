import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]
setuptools.setup(
    name="nodreader", # Replace with your own username
    version="0.0.1",
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
            'nr_resize = nodreader.resize:main',
            'nr_resize2 = nodreader.resize2:main',
        ],
    },
    install_requires=REQUIREMENTS,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
