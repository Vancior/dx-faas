import glob
import subprocess

for i in glob.glob('*.topo'):
    subprocess.run(['python', 'containernet_gen.py', i.split('.')[0]])
