#!/bin/bash
cd "$(dirname "$0")"/..

TRANSLATORS_FILE="weblate-translators.md"

function fileHeader {
  echo "# Weblate translations"
  echo -e "Special thanks to Weblate and the following users:\n"
}

function createTranslationCredits {
  declare -A translators

  while read; do
    author="${REPLY#Author: }"
    author="${author%% <*>}"

    read language
    language="${language#Translated using Weblate (}"
    language="${language%)}"

    thanksLine="$author for translating to $language"
    translators+=(["$thanksLine"]=true)
  done

  fileHeader
  for ty in "${!translators[@]}"; do
    echo " * $ty"
  done
  return 0
}

git log --no-merges --sparse --committer=weblate \
  | grep -E "Author: .*|Translated" \
  | createTranslationCredits | tee "$TRANSLATORS_FILE"
