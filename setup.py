from setuptools import setup

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "ReadMe.md").read_text()

setup(
    name='pyprofqueue',
    version='0.4.0',
    url='https://github.com/uksrc-developers/PyProfQueue',
    author='Marcus Keil',
    author_email='marcusk050291@gmail.com',
    license='MIT License',
    packages=['pyprofqueue'],
    package_dir={'pyprofqueue': 'pyprofqueue'},
    package_data={'pyprofqueue': ['../ReadMe.md',
                                  'batch_systems/*.py',
                                  'profilers/*.py',
                                  'profilers/data/*.txt',
                                  'profilers/data/read_prometheus.py']},
    install_requires=[
        'pytz',
        'h5py',
        'numpy',
        'tables',
        'pyarrow',
        'matplotlib',
        'pandas<=2.2.1',
        'promql_http_api==0.3.3'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.10',
    ],
    description="pyprofqueue serves as a python package that can take in existing bash scripts, add initialisations "
                "and calls to use profilers on the bash script, and submit the script to an HPC queue system on the "
                "users' behalf.",
    long_description=long_description,
    long_description_content_type='text/markdown',
)