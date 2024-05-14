from setuptools import setup

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "ReadMe.md").read_text()

setup(
    name='PyProfQueue',
    version='0.2.0',
    url='https://github.com/Marcus-Keil/PyProfQueue',
    author='Marcus Keil',
    author_email='marcusk050291@gmail.com',
    license='MIT License',
    packages=['PyProfQueue'],
    package_dir={'PyProfQueue': 'PyProfQueue'},
    package_data={'PyProfQueue': ['../ReadMe.md',
                                  'profilers/*.py',
                                  'profilers/data/*.txt',
                                  'profilers/data/read_prometheus.py']},
    install_requires=[
        'numpy',
        'pytz',
        'pyarrow',
        'matplotlib',
        'promql_http_api==0.3.3',
        'pandas<=2.2.1',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.10',
    ],
    description='A python package to inject profiling initialisation into bash scripts, translate queue options and '
                'submit jobs',
    long_description=long_description,
    long_description_content_type='text/markdown',
)