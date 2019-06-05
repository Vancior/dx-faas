import argparse
import json
import os
import sys
import time
import traceback

# from pprint import pprint

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    parser.add_argument('handler')
    parser.add_argument('--initializer', required=False, default='')
    return parser.parse_args()

"""
while True:
    headers = sys.stdin.readline()
    pprint(json.loads(headers), stream=sys.stderr)
    sys.stderr.flush()
    data = sys.stdin.readline()
    sys.stderr.write(data)
    sys.stderr.flush()
    # time.sleep(5)
    sys.stdout.write(json.dumps({'result': '这是结果'}, ensure_ascii=False))
    sys.stdout.flush()

"""
if __name__ == "__main__":
    stdin_backup = sys.stdin
    stdout_backup = sys.stdout
    stderr_backup = sys.stderr
    sys.stdin = open(os.devnull, 'r')
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

    while True:
        try:
            args = parse_args()
            if os.path.isdir('/data/function/_lib'):
                sys.path.insert(0, '/data/function/_lib')
            os.chdir('/data/function')
            code = compile(open(args.file).read(), args.file, 'exec')
            g = dict()
            exec(code, g, g)
            if args.initializer != '':
                result = g[args.initializer]()
                # if result is not None:
                #     stdout_backup.write(json.dumps(result))
                #     stdout_backup.flush()
            stdout_backup.write('ready')
            stdout_backup.flush()
            while True:
                headers = json.loads(stdin_backup.readline())
                body = stdin_backup.readline()
                try:
                    result = g[args.handler](headers, body)
                    stdout_backup.write(json.dumps(result, ensure_ascii=False))
                    stdout_backup.flush()
                except Exception as e:
                    traceback.print_tb(e.__traceback__, file=stderr_backup)
                    print(repr(e), file=stderr_backup)
                    stderr_backup.flush()
        except Exception as e:
            traceback.print_tb(e.__traceback__, file=stderr_backup)
            print(repr(e), file=stderr_backup)
            stderr_backup.flush()
            time.sleep(10)  # give time for stderr transmission
