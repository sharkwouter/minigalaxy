from setuptools import setup, find_packages
from glob import glob
import subprocess
from minigalaxy.version import VERSION

# Generate the translations
subprocess.run(['scripts/compile-languages.sh'])

setup(
    name="Minigalaxy",
    version=VERSION,
    packages=find_packages(),
    scripts=['bin/minigalaxy'],

    data_files=[
        ('share/applications', ['data/minigalaxy.desktop']),
        ('share/icons/hicolor/192x192/apps', ['data/minigalaxy.png']),
        ('share/minigalaxy/ui', glob('data/ui/*.ui')),
        ('share/metainfo', ['data/minigalaxy.metainfo.xml']),

        # Add translations
        ('share/minigalaxy/translations/nl/LC_MESSAGES/', ['data/mo/nl/LC_MESSAGES/minigalaxy.mo']),
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
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ]
)
