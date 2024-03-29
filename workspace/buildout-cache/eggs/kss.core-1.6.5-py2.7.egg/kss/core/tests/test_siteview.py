import doctest
import unittest
import zope.component.event # import does the trick
from zope.testing.cleanup import cleanUp
from zope.component.hooks import setHooks


def setUp(test=None):
    setHooks()


def tearDown(test=None):
    cleanUp()


def test_suite():
    return unittest.TestSuite([
        doctest.DocFileSuite('siteview.txt',
                             package='kss.core',
                             setUp=setUp,
                             tearDown=tearDown)
        ])
