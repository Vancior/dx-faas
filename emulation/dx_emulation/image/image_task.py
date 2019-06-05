import base64
import cv2
import json
import logging
import numpy as np
import os
import random
import time
from dx_emulation.utils import *

logger = logging.getLogger('Image Task')


def get_meta():
    start_time = os.getenv('START_TIME', default=0)
    start_time = int(start_time)
    run_interval = os.getenv('RUN_INTERVAL', default=1)
    run_interval = float(run_interval)
    run_count = os.getenv('RUN_COUNT')
    run_count = int(run_count)
    log_file = os.getenv('LOG_FILE')
    return {'start_time': start_time, 'run_interval': run_interval, 'log_file': log_file, 'run_count': run_count}


def relative_path(path):
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), path))


def run():
    meta = get_meta()
    time.sleep(meta['start_time'])
    log_file = open(meta['log_file'], 'w')
    run_count = meta['run_count']
    image = cv2.imread(relative_path('t3.jpg'))
    ret, jpg_np = cv2.imencode('.jpg', image)
    if ret:
        jpg_bytes = base64.b85encode(jpg_np)
        data = {'image': jpg_bytes.decode('ascii')}
    else:
        raise RuntimeError('cv2.imencode failed')

    request_count = 3
    while request_count > 0:
        try:
            token_manager = TokenManager()
            function_service = FunctionService(token_manager, timeout=None)
            t1 = time.time()
            function_service.request('face-detection')
            t1 = time.time() - t1
            log_file.write(f'request {t1}\n')
            while run_count > 0:
                try:
                    t1 = time.time()
                    data['time'] = t1
                    body, header = function_service.call(
                        'face-detection', json.dumps(data), {'Content-Type': 'application/json'})
                    t1 = time.time() - t1
                    log_file.write(f'call {t1}\n')
                    run_count -= 1
                    # body = json.loads(body)
                    logger.info(body)
                except FunctionExpireError:
                    function_service.request('face-detection')
                except Exception as e:
                    log_file.write('call -1\n')
                    run_count -= 1
                    logger.error(repr(e))
            if run_count == 0:
                request_count = 0
        except Exception as e:
            logger.error(e)
            time.sleep(5)
            request_count -= 1
