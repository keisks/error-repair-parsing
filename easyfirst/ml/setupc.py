from distutils.core import setup, Extension

setup (name = 'ml',
		version = '1.0',
		ext_modules = [
         Extension('ml', sources = ['ml.c']),
         Extension('sml', sources = ['sml.c']]))

