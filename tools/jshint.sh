#!/bin/sh

set -e

VERSION=2.9.2
BASE=$HOME/install-jshint

action=$1
shift

case $action in
    install)
        rm -rf "$BASE"
        mkdir "$BASE"
        cd "$BASE"
        npm install jshint@$VERSION
        ;;

    run)
        "$BASE/node_modules/.bin/jshint" "$@"
        ;;
esac
