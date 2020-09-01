import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="execdmscript",
    version="1.0.1",
    author="miile7",
    author_email="miile7@gmx.de",
    description=("A python module for executing DM-Script from python in the " + 
                 "Gatan Microscopy Suite® (GMS) (Digital Micrograph)"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/miile7/execdmscript",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics"
    ],
    python_requires='>=3.5',
)