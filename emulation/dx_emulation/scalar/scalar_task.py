import json
import logging
import os
import random
import time
from dx_emulation.utils import *

logger = logging.getLogger('scalar-task')


def get_meta():
    start_time = os.getenv('START_TIME', default=0)
    start_time = int(start_time)
    run_interval = os.getenv('RUN_INTERVAL', default=1)
    run_interval = float(run_interval)
    run_count = os.getenv('RUN_COUNT')
    run_count = int(run_count)
    log_file = os.getenv('LOG_FILE')
    return {'start_time': start_time, 'run_interval': run_interval, 'log_file': log_file, 'run_count': run_count}


def run():
    # NOTE wait for a period of time to emulate random timing access
    meta = get_meta()
    time.sleep(meta['start_time'])
    log_file = open(meta['log_file'], 'w')
    run_count = meta['run_count']

    while True:
        try:
            token_manager = TokenManager()
            function_service = FunctionService(token_manager, timeout=None)
            t1 = time.time()
            function_service.request('temp-convert')
            t1 = time.time() - t1
            log_file.write(f'request {t1}\n')
            # logger.info(f'request function time: {time.time()-t1}')
            while run_count > 0:
                try:
                    celsius = random.randint(0, 100)
                    t1 = time.time()
                    body, header = function_service.call(
                        'temp-convert', json.dumps({'c': celsius}),
                        {'Content-Type': 'application/json'})
                    # logger.info(f'response time: {time.time()-t1}')
                    t1 = time.time() - t1
                    log_file.write(f'call {t1}\n')
                    run_count -= 1
                    body = json.loads(body)
                    # logger.info(
                    #     f'Celsius: {celsius} -> Fahrenheit: {body["f"]}')
                except FunctionExpireError:
                    function_service.request('temp-convert')
                except Exception as e:
                    log_file.write('call -1\n')
                    run_count -= 1
                    logger.error(repr(e))
                time.sleep(meta['run_interval'])
            log_file.flush()
            log_file.close()
            break
        except Exception as e:
            # except FunctionRequestTimeout as e:
            logger.error(e)
            time.sleep(5)
