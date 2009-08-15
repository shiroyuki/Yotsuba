from setuptools import setup

setup(
    name='yotsuba',
    version='2.0',
    description='Software Development Kit for new Python Developers',
    author='Juti Noppornpitak',
    author_email='juti_n@yahoo.co.jp',
    url='http://yotsuba.shiroyuki.com',
    packages=['yotsuba'],
    long_description='Yotsuba is a library and a software development kit for new Python developers.',
    classifiers=[
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries"
    ],
    keywords='Web, XML, Mail, API, SDK',
    license='LGPL',
    install_requires=[
      'setuptools',
    ]
)
