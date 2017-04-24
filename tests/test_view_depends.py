#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
test_view_depends
Test Views and Depends
:copyright: 2017 by Amine Tedjini &amp; Consulting (P) Limited
:license: BSD, see LICENSE for more details.
'''
import sys
import os

DIR = os.path.abspath(os.path.normpath(os.path.join(__file__, '..', '..', '..', '..', '..', 'trytond')))
    if os.path.isdir(DIR):
        sys.path.insert(0, os.path.dirname(DIR))

import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_view, test_depends
      


class TestViewDependsCase(unittest.TestCase):
    '''
       Test the view and depends
    '''
    def setUp(self):
        trytond.tests.test_tryton.install_module('hr')


    def test0005views(self):
       '''
       Test views.
       '''
       test_view('hr')


    def test0006depends(self):
        '''
        Test depends.
        '''
        test_depends()


    def suite():
        test_suite = trytond.tests.test_tryton.suite()
        test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestViewDependsCase)
        return test_suite
        if __name__ == '__main__':
            unittest.TextTestRunner(verbosity=2).run(suite()

