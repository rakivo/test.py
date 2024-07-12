#!/usr/bin/env python3

# Copyright 2024 Mark Tyrkba <marktyrkba456@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import argparse as ap
import subprocess as sp

from itertools import takewhile

parser = ap.ArgumentParser()

parser.add_argument('-r',  '--record',       action='store_true',      help='Record expected outputs')
parser.add_argument('-f',  '--filter',       action='store', type=str, help='Filter files in directory(by extension), for example: `.py`', nargs='+')
parser.add_argument('-d',  '--dir',          action='store', type=str, help='Path to directory', required=True)
parser.add_argument('-ed', '--expected_dir', action='store', type=str, help='Path to directory in which expected outputs will be stored', default='expected')
parser.add_argument('-c',  '--command',      action='store', type=str, help='Command to execute to get output, for example: `python $`, where $ is a path to file we are currently proccesing', nargs='+')
parser.add_argument('-rng',  '--range',      action='store', type=str, help='Range of lines that will be used as a frame to compare "expected" and real output. The range should be provided in the format "start..end", where "start" and "end" are the zero-based line numbers (non-inclusive) that define the range, just like in Rust. For example, `-r 5..15` would use the lines from 5 to 15 as the expected output, additionally, you can use relative indexes, for example: `-r 1..e6`, which means, end will be calculated as: len(output.lines()) - end')

args = parser.parse_args()

LOG_CMD   = '[CMD]'
LOG_INFO  = '[INFO]'
LOG_WARN  = '[WARN]'
LOG_PANIC = '[PANIC]'
LOG_ERROR = '[ERROR]'

if not os.path.exists(args.expected_dir):
    os.makedirs(args.expected_dir)

if not os.path.exists(args.dir):
    print(LOG_PANIC, f'`{args.dir}` does not exist')
    exit(1)

SEPARATOR = '----------------------------------'

END_SYMBOL = 'e'
FILE_SYMBOL = '$'

FILES = os.listdir(args.dir)

def pattern_match_command(f: str) -> str:
    if FILE_SYMBOL in args.command:
        return ' '.join([f if x == FILE_SYMBOL else x for x in args.command])
    else:
        print(LOG_WARN, f'-cmd flag args does not contain any {FILE_SYMBOL} to match files')
        return f

def is_file_matches(ext: str) -> bool:
    if not args.filter:
        return True

    return any(map(lambda e: e == ext, args.filter))

def get_expected_file_path(file_name: str) -> str:
    return os.path.join(args.expected_dir, file_name + '.txt')

def process_output(output_lines: list[str]) -> list[str]:
    if not args.range: return output_lines

    if '..' not in args.range:
        print(LOG_PANIC, 'provided range must be in start..end format')
        exit(1)

    start = 0 if args.range.startswith('..') else int(''.join(takewhile(lambda x: x != '.', args.range)))
    if start < 0 or start >= len(output_lines):
        print(LOG_PANIC, f'invalid start index: {end}, maximum index possible: {len(output_lines)}')
        exit(1)

    end = len(output_lines) if args.range.endswith('..') else int(''.join(reversed(list(takewhile(lambda x: x.isdigit(), reversed(args.range))))))
    if end < 0 or end > len(output_lines):
        print(LOG_PANIC, f'invalid end index: {end}, maximum index possible: {len(output_lines)}')
        exit(1)

    end = end if not END_SYMBOL in args.range else len(output_lines) - end - 1
    return output_lines[start:end]

def cmd(args: list[str]) -> str:
    print(LOG_CMD, *args)
    result = sp.run(' '.join(args), text=True, shell=True, capture_output=True)

    if result.returncode != 0:
        print(LOG_PANIC, f'Process exited abnormally with code {result.returncode}')
        print(LOG_PANIC, result.stderr, end='')
        exit(1)

    return result.stdout

def record_examples():
    print(SEPARATOR)
    print(LOG_INFO, 'Recording examples')
    print(SEPARATOR)

    for f in FILES:
        name, ext = os.path.splitext(f)
        if not is_file_matches(ext): continue

        file_path = os.path.join(args.dir, f)
        command = pattern_match_command(file_path)
        output = process_output(cmd([command]).split('\n'))
        expected_file_path = get_expected_file_path(name)
        with open(expected_file_path, 'w') as expected:
            print(f'Writing to: {expected_file_path}..')
            print(SEPARATOR)
            expected.write('\n'.join(output))

def test_examples():
    if not args.record: print(SEPARATOR)
    print(LOG_INFO, 'Testing examples')
    print(SEPARATOR)

    for f in FILES:
        name, ext = os.path.splitext(f)
        if not is_file_matches(ext): continue

        file_path = os.path.join(args.dir, f)
        command = pattern_match_command(file_path)
        got = '\n'.join(process_output(cmd([command]).split('\n')))
        expected_file_path = get_expected_file_path(name)
        with open(expected_file_path, 'r') as expected:
            expected = expected.read()
            print(SEPARATOR)
            print(LOG_INFO, f'Comparing output with: {expected_file_path}')
            if got.strip() == expected.strip():
                print(LOG_INFO, f'`{name}` test: OK')
            else:
                print(LOG_PANIC, f'`{name}`: FAILED')
                print(LOG_PANIC, f'Got: {got}\nExpected: {expected}')
            print(SEPARATOR)

if __name__ == '__main__':
    if args.record:
        record_examples()
    test_examples()
