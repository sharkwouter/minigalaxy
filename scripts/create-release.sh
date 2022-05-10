#!/bin/bash
set -e

# Set variables
cd "$(dirname "$0")/.."

WORK_DIR="${PWD}"
SCRIPT_DIR="${WORK_DIR}/scripts"
CHANGELOG_FILE="${WORK_DIR}/CHANGELOG.md"
METADATA_FILE="${WORK_DIR}/data/io.github.sharkwouter.Minigalaxy.metainfo.xml"
RELEASE_FILE="${WORK_DIR}/release.md"
VERSION_FILE="${WORK_DIR}/minigalaxy/version.py"
VERSION="$(head -1 "${CHANGELOG_FILE}"|tr -d "*")"

check_changelog() {
  "${SCRIPT_DIR}/check-changelog.sh" > /dev/null
}

init_release_file() {
  echo "Minigalaxy version ${VERSION} is now available. For new users, Minigalaxy is a simple GOG client for Linux. The download and a breakdown of the changes can be found below." > "${RELEASE_FILE}"
  echo "" >> "${RELEASE_FILE}"
  echo "![screenshot](https://raw.githubusercontent.com/sharkwouter/minigalaxy/1.1.0/screenshot.jpg)" >> "${RELEASE_FILE}"
  echo "" >> "${RELEASE_FILE}"
  echo "## Changes" >> "${RELEASE_FILE}"
  echo "" >> "${RELEASE_FILE}"
}

add_release_file_entry() {
  echo " - $@" >> "${RELEASE_FILE}"
}

finish_release_file() {
  echo "" >> "${RELEASE_FILE}"
  echo "As usual, a deb file for installing this release on Debian and Ubuntu can be found below. Packages most distributions will most likely become available soon. See the [website](https://sharkwouter.github.io/minigalaxy/) for installation instructions.">> "${RELEASE_FILE}"
}

init_metadata() {
  xmlstarlet ed -L \
  -s /component/releases \
  -t elem -n "release version=\"${VERSION}\" date=\"$(date -Idate)\"" \
  "${METADATA_FILE}"

  xmlstarlet ed -L \
  -s /component/releases/release[@version="'$VERSION'"] \
  -t elem -n "description" \
  -s /component/releases/release[@version="'$VERSION'"]/description \
  -t elem -n "p" -v "Implements the following changes:" \
  -s /component/releases/release[@version="'$VERSION'"]/description \
  -t elem -n "ul" \
  "${METADATA_FILE}"
}

add_metadata_entry() {
  xmlstarlet ed -L \
  -s /component/releases/release[@version="'$VERSION'"]/description/ul \
  -t elem -n li -v "$(echo $@|sed 's/^- //')" \
  "${METADATA_FILE}"
}

add_debian_changelog_entry() {
  dch -v "${VERSION}" -M "$(echo $@|sed 's/^- //')"
}

set_debian_changelog_release() {
  dch -r -D "$(lsb_release -cs)" ""
}

set_version() {
  echo "VERSION = \"${VERSION}\"" > "${VERSION_FILE}"
}

return_version_info() {
  echo "::set-output name=VERSION::${VERSION}"
}

###############
# Actual code #
###############

check_changelog

set_version
init_metadata
init_release_file

n=0
while read line; do
  n=$((n+1))
  if [ $n -eq 1 ] || [ -z "${line}" ]; then
    continue
  fi

 # End the loop if we find the next version
  if [[ "${line}" =~ ^\*\*[0-9]*\.[0-9]*\.[0-9]*\*\*$ ]]; then
    break
  fi

  line="$(echo ${line}|sed 's/^- //')"
  add_metadata_entry "${line}"
  add_release_file_entry "${line}"
  add_debian_changelog_entry "${line}"

done < "${CHANGELOG_FILE}"

set_debian_changelog_release
finish_release_file
return_version_info
