import os
import sys
from setuptools import setup, find_packages

version='0.2'

def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()


setup(name='pyhogan',
      version=version,
      description=('Mustache to javascript compiler.'),
      long_description='\n\n'.join((read('README.rst'), read('CHANGES.txt'))),
      classifiers=[
          "License :: OSI Approved :: Apache Software License",
          "Intended Audience :: Developers",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: Implementation :: CPython"],
      author='Nikolay Kim',
      author_email='fafhrd91@gmail.com',
      url='https://github.com/fafhrd91/pyhogan/',
      license='Apache Software License',
      py_modules=['pyhogan'],
      install_requires=['setuptools'],
      include_package_data=True,
      zip_safe=False,
      entry_points = {
        'console_scripts': [
            'pyhogan = pyhogan:main',
            ]
        },
      )
