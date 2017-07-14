#!/bin/sh

set -e

VERSION=4.2.0
BASE=$HOME/install-eslint

action=$1
shift

case $action in
    install)
        rm -rf "$BASE"
        mkdir "$BASE"
        cd "$BASE"
        npm install eslint@$VERSION
        ;;

    run)
        "$BASE/node_modules/.bin/eslint" "$@"
        ;;
esac
