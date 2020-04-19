#!/bin/bash

set -e

DIR=$(cd -P -- "$(dirname -- "$0")" && cd .. && pwd -P)

CONFIG="$DIR/webpack/config.prod.js"
DEST="$DIR/static/tmp/prod-stats.json"

NODE_ENV=production node_modules/.bin/webpack --config $CONFIG --profile --json > $DEST

webpack-bundle-analyzer $DEST

