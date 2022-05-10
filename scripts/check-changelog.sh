#!/bin/bash
cd "$(dirname "$0")"/..

n=0
while read line; do
  n=$((n+1))
  if [ $n -eq 1 ];then
    if [[ ! "${line}" =~ ^\*\*[0-9]*\.[0-9]*\.[0-9]*\*\*$ ]]; then
      echo "First line in CHANGELOG.md doesn't match **1.0.0** format"
      exit 1
    fi
    version="$(echo ${line}|tr -d "*")"
    echo "version: ${version}"
    continue
  fi

  if [ -z "${line}" ]; then
    continue
  fi

  if [[ "${line}" =~ ^\*\*[0-9]*\.[0-9]*\.[0-9]*\*\*$ ]]; then
    break
  fi

  echo "${line}"
  if [[ ! "${line}" =~ ^\ *-\ .* ]]; then
    echo "Error on line ${n} in CHANGELOG.md does not start with \"- \""
    exit 2
  fi
done < CHANGELOG.md
