Fuzzing HTTPolice with american fuzzy lop
=========================================

As a program that does complex processing on compact input files,
HTTPolice is amenable to testing with a dumb fuzzer such as
`american fuzzy lop`_.

As of this writing, all the bugs thus found have been discovered while
fuzzing original (valid) examples -- that is, AFL's genetic algorithm
has yet to bear fruit -- but the examples it produces do look interesting,
so perhaps if one were to run AFL seriously for a longer period of time,
more subtle bugs could be uncovered.

.. _american fuzzy lop: http://lcamtuf.coredump.cx/afl/


How to run
----------

Install american fuzzy lop as appropriate for your platform, for example::

  $ sudo apt-get install afl

Set up the environment::

  $ pip install Cython
  $ pip install python-afl
  $ fuzz_path=/some/working/directory
  $ mkdir -p $fuzz_path/examples

Prepare examples for AFL::

  $ tools/afl/prepare_examples.sh -n 100 $fuzz_path/examples/

Run it::

  $ AFL_NO_VAR_CHECK=1 \
      py-afl-fuzz -m 1000 -t 1000 \
      -i $fuzz_path/examples/ -o $fuzz_path/results/ -f $fuzz_path/input \
      -d -x tools/afl/http-tweaks.dict \
      -- python tools/afl/harness.py -i combined -o html $fuzz_path/input

Almost all paths are considered 'variable' by AFL. I'm not sure why.
Clearing the parser memo on every run doesn't help, but maybe it's
the memoization in grammar symbols. Anyway, this variability doesn't seem to be
a problem, and setting ``AFL_NO_VAR_CHECK=1`` greatly reduces the time spent
on calibration.

Remove the ``-d`` option if you have patience.

The crash deduper in AFL is conservative enough that it reports many more
'unique' crashes than are actually unique, so don't be alarmed by numbers
like 50 or 100. Also, a fair number of spurious hangs is detected.
