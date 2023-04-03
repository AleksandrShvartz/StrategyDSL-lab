from setuptools import setup
from Cython.Build import cythonize

setup(
    name='Kalah',
    ext_modules=cythonize("kalah.pyx"),
    zip_safe=False,
)
