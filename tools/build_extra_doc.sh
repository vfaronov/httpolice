#!/bin/sh

# Prepare files to be uploaded to pythonhosted.org.
# XXX: when changing this file,
# you may also need to change ``extra_doc_hack.sh``.

set -e

dir=extra_doc
build_dir=$dir/_build
rm -rf "$dir" "$build_dir"
mkdir -p "$dir" "$build_dir"

echo 'Generating notices list...'
python tools/list_notices.py >"$build_dir/notices.html"

echo 'Generating showcase report...'
httpolice -i combined -o html test/combined_data/showcase.https \
    >"$build_dir/showcase.html"

echo 'Generating redirects to Read the Docs...'
for name in api concepts django genindex har index install mitmproxy \
            py-modindex quickstart reports search streams
do
    new_url="http://httpolice.readthedocs.io/en/stable/$name.html"
    cat >"$build_dir/$name.html" <<EOF
<!DOCTYPE html>
<html>
    <head>
        <title>HTTPolice documentation</title>
        <meta http-equiv="content-type" content="text/html; charset=utf-8">
        <meta http-equiv="refresh" content="0; url=$new_url">
    </head>
    <body>
        <p>
            The HTTPolice user manual has moved to
            <a href="$new_url">Read the Docs</a>.
        </p>
        <p>
            If you are not redirected automatically, click here:
            <a href="$new_url">$new_url</a>
        </p>
    </body>
</html>
EOF
done

echo 'All done.'
