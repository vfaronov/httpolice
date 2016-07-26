#!/bin/sh

# Download and run a local copy of the `Nu Html Checker`__.
# We do this (rather than simply upload to the online public instance)
# in order to pin down the version of the checker
# and thus ensure reproducibility.
#
# __ http://validator.github.io/validator/

set -e

RELEASES=https://github.com/validator/validator/releases
VERSION=16.6.29

JAVA=/usr/lib/jvm/java-8-oracle/bin/java
test -e "$JAVA" || JAVA=java

action=$1
shift

case $action in
    install)
        rm -rf vnu
        mkdir vnu
        cd vnu
        wget "$RELEASES/download/$VERSION/vnu.jar_$VERSION.zip" -O vnu.zip
        unzip vnu.zip
        ;;

    validate)
        "$JAVA" -jar vnu/dist/vnu.jar "$@"
        ;;
esac
