from distutils.core import setup

setup(
    name='slackchannel2pdf',
    version='0.4.0',
    author='Erik Kalkoken',
    packages=['slackchannel2pdf',],
    license='LICENSE',
    description='slackchannel2pdf is a command line tool for exporting the text contents of any Slack channel to a PDF file',
    long_description=open('README.md').read()
)