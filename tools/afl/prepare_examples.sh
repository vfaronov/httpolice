#!/bin/sh

# Take a sample of test cases from ``test/combined_data/``.
# The default sample size of 100 ensures that we seed the fuzzer with
# examples of many different protocol features (headers, methods etc.).
# Alternatively, maybe one could use a dictionary and try to make AFL
# generate these features on its own, but I don't have the time for that.

n=100
getopts n: OPT && [ "$OPT" = "n" ] && n=$OPTARG
shift $(( OPTIND - 1 ))

output_dir=$1

find test/combined_data/ | shuf -n "$n" | while read fn
do
    name="$( basename "$fn" )"
    test "$( stat -c %s "$fn" )" -lt 1000 || continue     # Skip large examples
    grep -vE --text '^# ' "$fn" >"$output_dir/$name"      # Remove comments
done
