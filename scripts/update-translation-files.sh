#!/bin/bash
cd "$(dirname "$0")"/..

POTFILE="data/po/minigalaxy.pot"

# Generate the pot file
xgettext --from-code=UTF-8 --keyword=_ --sort-output --add-comments --language=Python minigalaxy/*.py minigalaxy/ui/*.py bin/minigalaxy -o "${POTFILE}"
xgettext --join-existing --from-code=UTF-8 --keyword=translatable --sort-output --language=Glade data/ui/*.ui -o "${POTFILE}"

# Update each po file
for langfile in data/po/*.po; do
	msgmerge -U "${langfile}" "${POTFILE}" -N
done
