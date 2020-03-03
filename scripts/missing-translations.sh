#!/bin/bash
cd "$(dirname "$0")"/..

# Update each po file
for langfile in data/po/*.po; do
	echo "file: ${langfile}"
	msgattrib --untranslated "${langfile}"
	echo ""
done
