#!/bin/bash

set -e

# Run an idempotent webpack build.  Webpack puts files in static/tmp/.
# Compare those files to static/dist/, and see if they've changed.  If so, move
# the files from static/tmp/ to static/dist/ and echo "Changed".  If the've not
# changed, blow away tmp and echo "No change".

# Directory one above the present file
DIR=$(cd -P -- "$(dirname -- "$0")" && cd .. && pwd -P)
SRC="$DIR/static/tmp/"
DEST="$DIR/static/dist/"
CONFIG="$DIR/webpack/config.prod.js"

cd $DIR

NODE_ENV=production node_modules/.bin/webpack --config $CONFIG > /dev/null

set +e
  diff "$SRC" "$DEST" > /dev/null
  DIFF_STATUS=$?
set -e

if [ "$DIFF_STATUS" -eq "0" ] ; then 
  rm -rf "$SRC"
  echo "No change"
else
  rm -rf "$DEST"
  mv "$SRC" "$DEST"
  echo "Changed"
fi
