from setuptools import setup, find_packages
import os
version = open(os.path.join("Products", "PloneGazette", "version.txt")).read().strip()
setup(name='Products.PloneGazette',
      version=version,
      description="An easy to use Newsletter Service for Plone",
      long_description=open("README.txt").read().decode('UTF8').encode('ASCII', 'replace') + '\n' +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='plone newsletter',
      author='Plone Collective',
      author_email='tiberiu@edw.ro',
      url='https://svn.plone.org/svn/collective/PloneGazette/branches/plone-2.5-compatible/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          "Products.TALESField",
          "collective.monkeypatcher",
          "eea.versions"
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
