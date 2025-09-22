from setuptools import setup, find_packages

setup(
    name="ckanext-datarequests",
    version="0.1.1",
    description="CKAN extension to manage data requests (veri istekleri).",
    long_description="A CKAN extension that allows users to create and discuss data requests. Anonymous users can view, authenticated users can create requests and comments, only sysadmins can change request status.",
    author="Your Name",
    license="AGPL",
    packages=find_packages(),
    namespace_packages=['ckanext'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "ckan>=2.9",
    ],
    entry_points="""
        [ckan.plugins]
        datarequests=ckanext.datarequests.plugin:DataRequestsPlugin
    """,
)
