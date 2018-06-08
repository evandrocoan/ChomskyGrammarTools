#! /usr/bin/env python
# -*- coding: utf-8 -*-


import os
import unittest

from debug_tools import getLogger
log = getLogger( 127, __name__ )


from .utilities import wrap_text


class TestingUtilities(unittest.TestCase):
    """
        Unit Tests for the Finite Automata
    """

    @classmethod
    def setUp(self):
        self.maxDiff = None

    def assertTextEqual(self, goal, results):
        """
            Remove both input texts indentation and trailing white spaces, then assertEquals() both
            of the inputs.
        """
        goal = wrap_text( goal )
        results = wrap_text( results )

        # print( goal.encode( 'ascii' ) )
        # print( results.encode( 'ascii' ) )
        self.assertEqual( goal, results )

