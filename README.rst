**HTTPolice** is a Python library and a suite of tools
for checking HTTP requests and responses according to the standards.

HTTP is a complex protocol that features many elements
(like headers and status codes) and intricate rules on their usage.
Developers often get parts of it slightly wrong.
Usually these mistakes are benign, but sometimes
they turn into logical bugs and interoperability problems.

HTTPolice is like a **“lint” for your HTTP messages**.
For example, if you are building a Web service,
you can instrument your existing tests with HTTPolice
to get instant feedback when your service responds
with a malformed header or an inappropriate status code.

HTTPolice was partly inspired by `REDbot`__, another QA tool for HTTP.
But the approach is different: instead of actively testing your server,
HTTPolice passively analyzes whatever messages you feed into it.
This makes it possible to use HTTPolice on requests and responses
captured from a real process or test suite.

__ https://redbot.org/
