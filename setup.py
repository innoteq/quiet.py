

from setuptools import setup
from setuptools.command.build_py import build_py
import ctypes.util
import subprocess
import os


class BuildPyCommand(build_py):
    """Custom build command."""

    def run(self):
        # check if libquiet.so is at system lib paths
        if not ctypes.util.find_library('quiet'):
            libquiet = os.path.join(os.path.dirname(
                __file__), 'quiet', 'libquiet.so')
            if not os.path.isfile(libquiet):
                # build libquiet.so
                subprocess.check_call(['bash', 'scripts/libs.sh'])

        build_py.run(self)


setup(
    name='quiet',
    version='0.1',
    description='Quiet Modem',
    author='Brian Armstrong, Yihui Xiong',
    author_email='brian.armstrong.ece+pypi@gmail.com',
    url='https://github.com/quiet/quiet.py',
    cmdclass={
        'build_py': BuildPyCommand,
    },
    packages=['quiet'],
    install_requires=['numpy==1.14.5', ],
    include_package_data=True,
    zip_safe=False
)
