import os


def ensure_dir(_dir):
    if not os.path.exists(_dir):
        os.makedirs(_dir)
