#!/bin/bash
cd "$(dirname "$0")"/..
xgettext --from-code=UTF-8 --keyword=translatable --keyword=_ --sort-output data/ui/*.ui minigalaxy/window/*.py -o data/po/minigalaxy.pot
