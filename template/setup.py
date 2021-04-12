import setuptools

REQUIRED_PACKAGES = [
    'google-cloud-storage==1.28.1',
    'smart-open==2.0.0'
]

PACKAGE_NAME = 'my_package'
PACKAGE_VERSION = '0.0.1'

setuptools.setup(
    name=PACKAGE_NAME,
    version=PACKAGE_VERSION,
    description='My setup file',
    install_requires=REQUIRED_PACKAGES,
    packages=setuptools.find_packages(),
)