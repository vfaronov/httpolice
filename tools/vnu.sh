#!/bin/sh

# Download and run a local copy of the `Nu Html Checker`__.
# We do this (rather than simply upload to the online public instance)
# in order to pin down the version of the checker
# and thus ensure reproducibility.
#
# __ http://validator.github.io/validator/

set -e

RELEASES=https://github.com/validator/validator/releases
VERSION=17.7.0

JAVA=/usr/lib/jvm/java-8-oracle/bin/java
test -e "$JAVA" || JAVA=java

BASE=$HOME/install-vnu

action=$1
shift

case $action in
    install)
        rm -rf "$BASE"
        mkdir "$BASE"
        cd "$BASE"
        wget "$RELEASES/download/$VERSION/vnu.jar_$VERSION.zip" -O vnu.zip
        unzip vnu.zip
        ;;

    run)
        "$JAVA" -jar "$BASE/dist/vnu.jar" "$@"
        ;;
esac
