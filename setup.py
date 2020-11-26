import os
from setuptools import find_packages, setup

from slackchannel2pdf import __version__


# read the contents of your README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="slackchannel2pdf",
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    license="MIT",
    description=(
        "slackchannel2pdf is a command line tool for exporting the text "
        "contents of any Slack channel to a PDF file"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Erik Kalkoken",
    author_email="kalkoken87@gmail.com",
    classifiers=[
        "Environment :: Console",
        "Environment :: Win32 (MS Windows)",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
    ],
    install_requires=[
        "Babel==2.7.0",
        "pytz==2019.1",
        "python-dateutil==2.8.0",
        "slackclient==2.1.0",
        "tzlocal==2.0.0",
    ],
    extras_require={"testing": ["PyPDF2", "coverage"]},
    entry_points={
        "console_scripts": [
            "slackchannel2pdf=slackchannel2pdf.run:main",
        ],
    },
)
