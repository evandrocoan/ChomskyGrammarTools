#! /usr/bin/env python
# -*- coding: utf-8 -*-


import os
import unittest

from debug_tools import getLogger
log = getLogger( 127, __name__ )

from .utilities import wrap_text
from grammar.lockable_type import LockableType


class TestingUtilities(unittest.TestCase):
    """
        Holds common features across all Unit Tests.
    """

    def setUp(self):
        """
            Called right before each Unit Test is ran, to setup new setting values.
        """

        ## Set the maximum size of the assertion error message when Unit Test fail
        self.maxDiff = None

    def tearDown(self):
        """
            Called right after each Unit Test finish its execution, to clean up settings values.
        """
        LockableType._USE_STRING = True

    def assertTextEqual(self, goal, results):
        """
            Remove both input texts indentation and trailing white spaces, then assertEquals() both
            of the inputs.
        """
        goal = wrap_text( goal, trim_tabs=True, trim_spaces=True )
        results = wrap_text( results, trim_tabs=True, trim_spaces=True )

        # print( goal.encode( 'ascii' ) )
        # print( results.encode( 'ascii' ) )
        self.assertEqual( goal, results )

