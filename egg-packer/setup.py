from setuptools import setup

setup(
    name='yotsuba',
    version='2.0-beta',
    description='Software Development Kit for Web Developers',
    author='Juti Noppornpitak',
    author_email='juti@primalfusion.com',
    url='http://yotsuba.shiroyuki.com',
    packages=['yotsuba'],
    long_description="""\
            Yotsuba is a software development kit for web developers.
        """,
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
