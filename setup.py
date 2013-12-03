from setuptools import setup, find_packages

setup(
    name='code-change-monitor',
    version='0.1+',
    description='Simple tool to count changes per developer in version control systems',
    author='Dustin J. Mitchell',
    author_email='dustin@mozilla.com',
    url='http://github.com/djmitche/code-change-monitor',
    install_requires=['sqlalchemy', 'approxidate'],
    tests_require=["nose", "mock"],
    packages=find_packages(),
    include_package_data=True,
    test_suite='nose.collector',
    entry_points="""
    [console_scripts]
        ccm-update = ccm.scripts.update:main
        ccm-users = ccm.scripts.users:main
        ccm-report = ccm.scripts.report:main
    """,
)
