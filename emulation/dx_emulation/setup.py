from distutils.core import setup

setup(name='dx-emulation',
      version='1.0',
      description='dx runtime python agent',
      author='Hu Juntao',
      author_email='hujuntao@buaa.edu.cn',
      packages=['dx_emulation', 'dx_emulation.utils', 'dx_emulation.scalar', 'dx_emulation.image', 'dx_emulation.scalar_f', 'dx_emulation.test_function'])
