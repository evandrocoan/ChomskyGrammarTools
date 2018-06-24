#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# Licensing
#
# Unit Tests Utilities
# Copyright (C) 2018 Evandro Coan <https://github.com/evandrocoan>
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation; either version 3 of the License, or ( at
#  your option ) any later version.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

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

