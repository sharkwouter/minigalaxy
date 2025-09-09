#!/bin/bash

_REPO_ROOT=$(dirname "$(readlink -f "$0")")
_REPO_ROOT=$(realpath "$_REPO_ROOT"/..)

cd "$_REPO_ROOT"

function createTranslationCredits {
  declare -A translators
  local author
  local language
  local thanksLine

  while read; do
    author="${REPLY#Author: }"
    author="${author%% <*>}"

    read language
    language="${language#Translated using Weblate (}"
    language="${language%)}"

    #text matches what is in readme
    thanksLine="- $author for translating to $language"
    # assign author as value for about.ui patching
    translators+=(["$thanksLine"]="$author")
  done

  declare -p translators
}

function patchAbout {
  local _STATE=""

  # this loop reads about.ui line-by-line
  while read; do

    # check the current line if it starts the translator-credits or ends that tag again
    case "$REPLY" in
      # just mark the start...
      *\<property\ name=\"translator-credits\"*)
        _STATE="BEGIN"
        ;;

      # ... to be able to recognize the next closing tag as belonging to the start
      # so we can patch in the weblate listing
      *\</property\>*)
        if [ "$_STATE" = "BEGIN" ]; then
          _STATE="DONE"
          # the terminating tag might be one the same line as something else
          _beforeEnd="${REPLY%%\</property\>*}"
          # whatever follows (if any) after the closing tag might also start a new sibling tag
          _afterEnd="${REPLY#*\</property\>}"

          # print whats before the closing tag if it is not from Weblate
          if [ -n "$_beforeEnd" ] && ! [[ "$_beforeEnd" =~ .*"(Weblate)".* ]]; then
            echo "$_beforeEnd"
          fi

          for weblate_author in "${translators[@]}"; do
            echo "$weblate_author (Weblate)"
          done

          echo "</property>"
          # change REPLY to whatever came after the closing tag
          REPLY="$_afterEnd"
        fi
        ;;
    esac

    # ignore previously generated weblate lines to re-create all of them
    # this is easier than merging
    if [[ "$REPLY" =~ .*"(Weblate)".* ]] || [ -z "$REPLY" ]; then
      continue
    fi

    echo "$REPLY"

  done <"$_REPO_ROOT/data/ui/about.ui"
}

function patchReadme {
  local _STATE
  declare -A alreadyAdded

  # this loop reads README.md line-by-line
  while read; do
    if [[ "$REPLY" =~ .*Special\ thanks.* ]]; then
      _STATE="PARSE"
    fi

    if [ "$_STATE" = "PARSE" ] && [ -n "$REPLY" ]; then
      alreadyAdded["$REPLY"]=true || echo "NOT WORKING: [$REPLY]" >2
    fi

  done <"$_REPO_ROOT/README.md"

  cat "$_REPO_ROOT/README.md"
  for thanksLine in "${!translators[@]}"; do
    if [ -z "${alreadyAdded["$thanksLine"]}" ]; then
      echo "$thanksLine"
    fi
  done
}

# 1. Pull the data from git log and place into an assoc 
#
# There is no direct way to return an array from a function.
# It is also not possible to declare a global one and pass it to the function for manipulation,
# because local manipulations will not propagate back.
# So the script re-declares it from the 'declare -p' function output
source <(git log --no-merges --sparse --committer=weblate --author='^(?!Wouter Wijsman).*$' --perl-regexp \
  | grep -E "^Author: .*|^\s*Translated using" \
  | createTranslationCredits)

# 2. patch into about
patchAbout > "$_REPO_ROOT/data/ui/about.ui.tmp"
mv -f "$_REPO_ROOT/data/ui/about.ui.tmp" "$_REPO_ROOT/data/ui/about.ui"

# 3. patch into readme
patchReadme > "$_REPO_ROOT/README.md.tmp"
mv -f "$_REPO_ROOT/README.md.tmp" "$_REPO_ROOT/README.md"
