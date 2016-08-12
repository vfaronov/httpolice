#!/bin/sh

set -e

VERSION=3.2.2
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
