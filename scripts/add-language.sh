#!/bin/bash
cd "$(dirname "$0")"/../data/po

if [ -z "${1}" ]; then
	echo "Please select a language like: ${0} en_US"
fi

msginit --locale="${1}" --input=minigalaxy.pot

LANGFILE="$(echo ${1}|cut -f1 -d'_').po"
xdg-open "${LANGFILE}"
