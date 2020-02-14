import sys
# if sys.version_info[0] < 3:
#     print("Python version detected:\n*****\n{0!s}\n*****\nCannot run, must be using Python 3".format(sys.version))
#     sys.exit()

from setuptools import setup, find_packages
from glob import glob

NAME = "tylerdurden"

setup(
    name = NAME,
    packages = find_packages(),
    include_package_data=True,
    version = '2019.9.18.0',
    license = 'GNU GPLv3',
    platforms = 'any',
    description = 'Redbuilds image using a bank of very small square images ("tiles")',
    author = 'Julio Trevisan',
    author_email = 'juliotrevisan@gmail.com',
    url = f'http://github.com/trevisanj/{NAME}',
    keywords= [],
    install_requires = ["a107", "Pillow"],
    python_requires = '>=3',
    scripts = glob(f'{NAME}/scripts/*.py')
)
