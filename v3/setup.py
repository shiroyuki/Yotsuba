from setuptools import setup, find_packages

setup(
    name = "yotsuba",
    version = "3.0",
    packages = find_packages(),
    install_requires = [
        "tenjin", "mako", "cherrypy", "pygments"
    ]
)
