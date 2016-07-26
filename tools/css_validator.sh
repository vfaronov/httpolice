#!/bin/sh

# There's no easy way to pin down the version of the CSS validator,
# but let's hope it doesn't break very often.

curl --silent --show-error --fail \
    https://jigsaw.w3.org/css-validator/validator \
    --form "file=@$1;type=text/css" --form output=soap12 | \
    # Show output for debug purposes
    tee /dev/stderr | \
    xmlstarlet sel --text -N m=http://www.w3.org/2005/07/css-validator \
        -t -v //m:errorcount -v //m:warningcount - | \
    # Exit with non-zero status if not both 0
    grep -Eq '^00$'
