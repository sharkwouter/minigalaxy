from setuptools import setup, find_packages
from glob import glob
from minigalaxy.version import VERSION
setup(
    name="Minigalaxy",
    version=VERSION,
    packages=find_packages(),
    scripts=['bin/minigalaxy'],

    data_files=[
        ('share/applications', ['data/minigalaxy.desktop']),
        ('share/pixmaps', ['data/minigalaxy.png']),
        ('share/minigalaxy/ui', glob('data/ui/*.ui')),
        ('share/docs/minigalaxy', ['LICENSE', 'THIRD-PARTY-LICENSES.md', 'README.md'])
    ],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires=[
        'PyGObject>=3.30',
        'requests',
    ],

    # metadata to display on PyPI
    author="Wouter Wijsman",
    author_email="wwijsman@live.nl",
    description="A simple GOG Linux client",
    keywords="GOG gog client gaming gtk Gtk",
    url="https://github.com/sharkwouter/minigalaxy",  # project home page, if any
    project_urls={
        "Bug Tracker": "https://github.com/sharkwouter/minigalaxy/issues",
        "Documentation": "https://github.com/sharkwouter/minigalaxy/blob/master/README.md",
        "Source Code": "https://github.com/sharkwouter/minigalaxy",
    },
    classifiers=[
        'License :: OSI Approved :: Gnu General Public License version 3'
    ]
)
