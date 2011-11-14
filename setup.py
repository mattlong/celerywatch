from setuptools import setup, find_packages

import celerywatch

setup(
    name="celerywatch",
    packages=find_packages(),
    version=celerywatch.VERSION,
    author="Matt Long",
    license="BSD",
    author_email="matt@mattlong.org",
    url="http://pypi.python.org/pypi/celerywatch/",
    description="Runs a celery app that monitors celeryd and stops it if it fails too many tasks.",
    long_description="Runs a celery app that monitors celeryd and stops it if it fails too many tasks.",
    install_requires=['django-celery==2.4.1'],
    zip_safe=False,
    #entry_points={
    #    'console_scripts': ['charon = charon.server:main',],
    #},
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
