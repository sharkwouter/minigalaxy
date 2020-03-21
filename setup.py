from setuptools import setup, find_packages
from glob import glob
import subprocess
from minigalaxy.version import VERSION

# Generate the translations
subprocess.run(['scripts/compile-translations.sh'])

setup(
    name="minigalaxy",
    version=VERSION,
    packages=find_packages(exclude=['tests']),
    scripts=['bin/minigalaxy'],

    data_files=[
        ('share/applications', ['data/com.github.sharkwouter.minigalaxy.desktop']),
        ('share/icons/hicolor/128x128/apps', ['data/icons/128x128/com.github.sharkwouter.minigalaxy.png']),
        ('share/icons/hicolor/192x192/apps', ['data/icons/192x192/com.github.sharkwouter.minigalaxy.png']),
        ('share/minigalaxy/ui', glob('data/ui/*.ui')),
        ('share/minigalaxy/images', glob('data/images/*')),
        ('share/metainfo', ['data/com.github.sharkwouter.minigalaxy.metainfo.xml']),

        # Add translations
        ('share/minigalaxy/translations/de/LC_MESSAGES/', ['data/mo/de/LC_MESSAGES/minigalaxy.mo']),
        ('share/minigalaxy/translations/fr/LC_MESSAGES/', ['data/mo/fr/LC_MESSAGES/minigalaxy.mo']),
        ('share/minigalaxy/translations/nb_NO/LC_MESSAGES/', ['data/mo/nb_NO/LC_MESSAGES/minigalaxy.mo']),
        ('share/minigalaxy/translations/nl/LC_MESSAGES/', ['data/mo/nl/LC_MESSAGES/minigalaxy.mo']),
        ('share/minigalaxy/translations/pl/LC_MESSAGES/', ['data/mo/pl/LC_MESSAGES/minigalaxy.mo']),
        ('share/minigalaxy/translations/pt_BR/LC_MESSAGES/', ['data/mo/pt_BR/LC_MESSAGES/minigalaxy.mo']),
        ('share/minigalaxy/translations/tr/LC_MESSAGES/', ['data/mo/tr/LC_MESSAGES/minigalaxy.mo']),
        ('share/minigalaxy/translations/zh_TW/LC_MESSAGES/', ['data/mo/zh_TW/LC_MESSAGES/minigalaxy.mo']),
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
