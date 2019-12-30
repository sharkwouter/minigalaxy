#!/bin/bash
cd "$(dirname "$0")"/../data/po

OUTPUTFILE="minigalaxy.mo"

for langfile in *.po; do
	
	OUTPUTDIR="../mo/$(echo ${langfile}|cut -f1 -d '.')/LC_MESSAGES"
	mkdir -p "${OUTPUTDIR}"
	msgfmt -o "${OUTPUTDIR}/${OUTPUTFILE}" "${langfile}"
done
