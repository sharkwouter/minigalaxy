from setuptools import setup, find_packages
from glob import glob
import subprocess
import os
import sys

sys.path.insert(0, os.getcwd())
from minigalaxy.version import VERSION  # noqa: E402

# Generate the translations
subprocess.run(['bash', 'scripts/compile-translations.sh'])

translations = []
for language_file in glob("data/mo/*/*/*.mo"):
    install_path = os.path.join("share/minigalaxy/translations", os.path.relpath(os.path.dirname(language_file), "data/mo"))
    translations.append((install_path, [language_file]))

setup(
    version=VERSION,
    packages=find_packages(exclude=['tests', 'tests.*']),

    data_files=[
        ('share/applications', ['data/io.github.sharkwouter.Minigalaxy.desktop']),
        ('share/icons/hicolor/128x128/apps', ['data/icons/128x128/io.github.sharkwouter.Minigalaxy.png']),
        ('share/icons/hicolor/192x192/apps', ['data/icons/192x192/io.github.sharkwouter.Minigalaxy.png']),
        ('share/metainfo', ['data/io.github.sharkwouter.Minigalaxy.metainfo.xml']),
    ] + translations,
)
