from setuptools import setup

setup(
    name='yotsuba',
    version='2.2',
    description='Software Development Kit for new Python Developers',
    author='Juti Noppornpitak',
    author_email='juti_n@yahoo.co.jp',
    url='http://yotsuba.shiroyuki.com',
    packages=['yotsuba'],
    long_description='Yotsuba is a library and a software development kit for new Python developers.',
    classifiers=[
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    keywords='Web, XML, Mail, API, SDK',
    license='LGPL',
    install_requires=[
      'setuptools',
    ]
)
