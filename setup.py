try:
    from setuptools import setup
except ImportError:
    # Fallback to the standard library distutils.
    from distutils.core import setup

exec(open('afsutil/__version__.py').read()) # sets VERSION

description='Utilities to setup OpenAFS clients and servers'
try:
    long_description = open('README.rst').read()
except:
    # Fallback if readme is not found.
    long_description = description

setup(
    name='afsutil',
    version=VERSION,
    description=description,
    long_description=long_description,
    author='Michael Meffie',
    author_email='mmeffie@sinenomine.net',
    url='https://github.com/openafs-contrib/afsutil',
    license='BSD',
    packages=[
        'afsutil',
        'afsutil.system',
    ],
    scripts=[
        'bin/afsutil',
    ],
    include_package_data=True,
    test_suite='test',
    zip_safe=False,
    options = {
        'bdist_rpm':{
            'post_install': 'packaging/rpm/post_install.sh',
            'post_uninstall': 'packaging/rpm/post_uninstall.sh',
        },
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: SunOS/Solaris',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
    ],
)
