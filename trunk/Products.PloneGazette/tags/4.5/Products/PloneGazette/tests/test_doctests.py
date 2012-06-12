""" Doctests
"""
import doctest
import unittest
from Products.PloneGazette.tests.base import PloneGazetteFunctionalTestCase
from Testing.ZopeTestCase import FunctionalDocFileSuite


OPTIONFLAGS = (
        doctest.REPORT_ONLY_FIRST_FAILURE |
        doctest.ELLIPSIS |
        doctest.NORMALIZE_WHITESPACE
)

def test_suite():
    """ Tests
    """
    return unittest.TestSuite((
            FunctionalDocFileSuite('README.txt',
                  optionflags=OPTIONFLAGS,
                  package='Products.PloneGazette',
                  test_class=PloneGazetteFunctionalTestCase),
              ))
