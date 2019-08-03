from distutils.core import setup

setup(
    name='channelexport',
    version='0.4.0',
    author='Erik Kalkoken',
    packages=['channelexport',],
    license='LICENSE',
    description='channelexport is a command line tool for exporting the text contents of any Slack channel to a PDF file',
    long_description=open('README.md').read()
)