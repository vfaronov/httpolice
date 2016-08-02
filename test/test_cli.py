# -*- coding: utf-8; -*-

import os

import httpolice.cli
from httpolice.util.text import MockStdio


base_path = os.path.dirname(__file__)


def run(options, relative_paths):
    argv = ['httpolice'] + options + [os.path.join(base_path, relative_path)
                                      for relative_path in relative_paths]
    stdout = MockStdio()
    stderr = MockStdio()
    args = httpolice.cli.parse_args(argv)
    exit_status = httpolice.cli.run_cli(args, stdout, stderr)
    return (exit_status, stdout.buffer.getvalue(), stderr.buffer.getvalue())


def test_basic():
    (code, stdout, stderr) = run(['-i', 'combined'],
                                 ['combined_data/simple_ok'])
    assert code == 0
    assert stdout == b''
    assert stderr == b''


def test_basic_html():
    (code, stdout, stderr) = run(['-i', 'combined', '-o', 'html'],
                                 ['combined_data/simple_ok'])
    assert code == 0
    assert b'<!DOCTYPE html' in stdout
    assert b'User-Agent' in stdout
    assert stderr == b''


def test_fail_on():
    (code, stdout, stderr) = run(['-i', 'combined', '--fail-on=comment'],
                                 ['combined_data/simple_ok'])
    assert code == 0
    assert stdout == b''
    assert stderr == b''

    (code, stdout, stderr) = run(['-i', 'combined', '--fail-on=comment'],
                                 ['combined_data/simple_ok',
                                  'combined_data/1003_1'])
    assert code == 0
    assert b'D 1003' in stdout
    assert stderr == b''

    (code, stdout, stderr) = run(['-i', 'combined', '--fail-on=comment'],
                                 ['combined_data/simple_ok',
                                  'combined_data/1250_1'])
    assert code > 0
    assert b'C 1250' in stdout
    assert stderr == b''

    (code, stdout, stderr) = run(['-i', 'combined', '--fail-on=comment'],
                                 ['combined_data/simple_ok',
                                  'combined_data/1172_1'])
    assert code > 0
    assert b'E 1172' in stdout
    assert stderr == b''


def test_bad_combined_file():
    (code, stdout, stderr) = run(['-i', 'combined'],
                                 ['har_data/simple_ok.har'])
    assert code > 0
    assert stdout == b''
    assert b'bad combined file' in stderr


def test_har():
    (code, stdout, stderr) = run(['-i', 'har'], ['har_data/simple_ok.har'])
    assert code == 0
    assert stdout == b''
    assert stderr == b''


def test_bad_har_file_1():
    (code, stdout, stderr) = run(['-i', 'har'], ['combined_data/simple_ok'])
    assert code > 0
    assert stdout == b''
    assert b'bad HAR file' in stderr
    assert b'Traceback' not in stderr


def test_bad_har_file_2():
    (code, stdout, stderr) = run(['-i', 'har'], ['misc_data/bad.har'])
    assert code > 0
    assert stdout == b''
    assert b'cannot understand HAR file' in stderr
    assert b'Traceback' not in stderr


def test_tcpflow():
    (code, stdout, stderr) = run(['-i', 'tcpflow'],
                                 ['tcpflow_data/request_timeout'])
    assert code == 0
    assert b'C 1278' in stdout
    assert stderr == b''


def test_bad_tcpflow_directory():
    (code, stdout, stderr) = run(['-i', 'tcpflow'],
                                 ['tcpflow_data/wrong_filenames'])
    assert code > 0
    assert stdout == b''
    assert b'wrong tcpflow filename' in stderr


def test_full_traceback():
    (code, stdout, stderr) = run(['-i', 'har', '--full-traceback'],
                                 ['combined_data/simple_ok'])
    assert code > 0
    assert stdout == b''
    assert b'bad HAR file' in stderr
    assert b'Traceback' in stderr


def test_silence():
    (code, stdout, stderr) = run(['-i', 'combined', '--fail-on=error',
                                  '-s', '1227', '-s', '1187'],
                                 ['combined_data/1187_1'])
    assert code == 0
    assert b'1187' not in stdout
    assert b'1183' in stdout
    assert stderr == b''
