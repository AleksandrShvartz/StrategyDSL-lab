from Cython.Build import cythonize
from setuptools import setup

setup(
    name="Kalah",
    ext_modules=cythonize("kalah.pyx"),
    zip_safe=False,
)
