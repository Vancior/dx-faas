import coloredlogs
import logging
import os

mode = os.getenv('EMULATION_MODE')  # NOTE dev, test
if mode is not None:
    mode.lower()

if mode == 'dev':
    coloredlogs.install(level='DEBUG')
else:
    coloredlogs.install(level='WARNING')
