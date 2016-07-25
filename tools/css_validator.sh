#!/bin/sh

# There's no easy way to pin down the version of the CSS validator,
# but let's hope it doesn't break very often.

curl -si https://jigsaw.w3.org/css-validator/validator \
    -F "file=@$1;type=text/css" -F output=soap12 | \
    tee /dev/stderr | grep -q 'W3C-Validator-Status: Valid'
