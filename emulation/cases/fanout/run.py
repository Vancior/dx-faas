import glob
import os
import subprocess

runtime_id = os.urandom(2).encode('hex')
all_log = open('{}.all.log'.format(runtime_id), 'w')

for i in glob.glob('*.topo'):
    name = i.split('.')[0]
    f = name + '.py'
    runtime_id = os.urandom(3).encode('hex')
    subprocess.call(['python', f, runtime_id])
    all_log.write(name)
    all_log.write('\n')
    log_count = 0
    for ii in glob.glob('/home/hujuntao/log/device/*{}.log'.format(runtime_id)):
        with open(ii) as ff:
            log_count += 1
            while True:
                line = ff.readline()
                if line:
                    all_log.write(line)
                else:
                    break
    print('name: {}, count: {}'.format(name, log_count))
    all_log.flush()

all_log.flush()
all_log.close()
