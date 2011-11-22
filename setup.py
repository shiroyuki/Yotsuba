from setuptools import setup, find_packages

setup(
    name        = "yotsuba",
    version     = "3.1rc",
    packages    = find_packages(),
    install_requires = [
        'cherrypy',
        'mako',
        'sqlalchemy'
    ]
)
