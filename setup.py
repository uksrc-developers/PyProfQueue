from setuptools import setup

setup(
    name='PyProfQueue',
    version='0.1',
    description='A python package to inject profiling initialisation into bash scripts, translate queue options and '
                'submit jobs',
    url='https://github.com/Marcus-Keil/PyProfQueue',
    author='Marcus Keil',
    author_email='marcusk050291 at gmail dot com',
    license='MIT License',
    packages=['PyProfQueue'],
    package_dir={'PyProfQueue': 'PyProfQueue'},
    package_data={'PyProfQueue': ['data/*.txt', 'data/read_prometheus.py']},
    install_requires=[
        'numpy',
        'pytz',
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
)