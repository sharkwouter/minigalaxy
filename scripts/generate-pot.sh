#!/bin/bash
cd "$(dirname "$0")"/..

POTFILE="data/po/minigalaxy.pot"

# Generate the pot file
xgettext --from-code=UTF-8 --keyword=translatable --keyword=_ --sort-output data/ui/*.ui minigalaxy/window/*.py -o "${POTFILE}"

# Update each po file
for langfile in data/po/*.po; do
	msgmerge -U "${langfile}" "${POTFILE}"
done
