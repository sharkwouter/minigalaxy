# Variables
cd "$(dirname "$0")"/..

IMAGE="screenshot.jpg"

# Delete the old screenshot
rm -f ${IMAGE}

# Start Minigalaxy
bin/minigalaxy &

# Wait for Minigalaxy
sleep 5s

# Get the window id
WID="$(xwininfo -tree -root|grep Minigalaxy|tail -1|awk '{print $1}')"

# Make the screenshot
import -window "${WID}" -strip -trim "${PWD}/${IMAGE}" && kill %1
