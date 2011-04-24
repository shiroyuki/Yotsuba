from setuptools import setup, find_packages

setup(
    name        = "yotsuba",
    version     = "4.0",
    packages    = find_packages(),
    install_requires = [
        'cherrypy',
        'mako',
        'sqlalchemy'
    ]
)
