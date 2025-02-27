from setuptools import setup, find_packages
from glob import glob
import subprocess
import os
from minigalaxy.version import VERSION

# Generate the translations
subprocess.run(['bash', 'scripts/compile-translations.sh'])

translations = []
for language_file in glob("data/mo/*/*/*.mo"):
    install_path = os.path.join("share/minigalaxy/translations", os.path.relpath(os.path.dirname(language_file), "data/mo"))
    translations.append((install_path, [language_file]))

setup(
    name="minigalaxy",
    version=VERSION,
    packages=find_packages(exclude=['tests']),
    scripts=['bin/minigalaxy'],

    data_files=[
        ('share/applications', ['data/io.github.sharkwouter.Minigalaxy.desktop']),
        ('share/icons/hicolor/128x128/apps', ['data/icons/128x128/io.github.sharkwouter.Minigalaxy.png']),
        ('share/icons/hicolor/192x192/apps', ['data/icons/192x192/io.github.sharkwouter.Minigalaxy.png']),
        ('share/minigalaxy/ui', glob('data/ui/*.ui')),
        ('share/minigalaxy/images', glob('data/images/*')),
        ('share/minigalaxy/wine_resources', glob('data/wine_resources/*')),
        ('share/minigalaxy/', ['data/style.css']),
        ('share/metainfo', ['data/io.github.sharkwouter.Minigalaxy.metainfo.xml']),
    ] + translations,

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
