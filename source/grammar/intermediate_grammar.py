#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# Licensing
#
# Project Utilities
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

import time

from debug_tools import getLogger

from .symbols import NO_GRAMMAR_CHANGES
from debug_tools.utilities import wrap_text

log = getLogger( 127, __name__ )


class Stage(object):
    """
        Represents a point in the grammar history, to determine whether this the beginning of
        the history, middle or end.
    """

    def __init__(self, value):
        """
            Initializes the history with a history point constant.
        """
        ## The value of the current time constant
        self.value = value

    def __eq__(self, other):
        """
            Determines whether this stage history entry is equal or not to another one given.
        """

        if isinstance(self, other.__class__):
            return self.value == other.value

        return False

    def __str__(self):
        """
            Return the current history point stage name.
        """

        if self.value == IntermediateGrammar.BEGINNING:
            return ", Beginning"

        if self.value == IntermediateGrammar.END:
            return ", End"

        return ""


class IntermediateGrammar(object):
    """
        Represents a grammar operation history entry, to be parsed later.
    """

    ## A constant for the beginning of the time
    BEGINNING = 0

    ## A constant for the end of the time
    END = 1

    ## A constant for any point between the beginning and end of the time
    MIDDLE = 2

    def __init__(self, grammar, name, stage):
        """
            Creates a full history entry for the current state of the given `grammar`.
        """
        ## The precise time when this history entry was created, useful to merge history for different grammars
        self.timestamp = time.time()

        ## The string representation of the grammar saved
        self.grammar = str( grammar )

        ## The name of the operation which originates the current grammar history entry
        self.name = name

        ## The stage name for the current grammar state
        self.stage = Stage( stage )

        ## Additional information to be displayed
        self.extra_text = []

    def __str__(self):
        """
            Return the full history representation of the saved grammar.
        """


        if self.extra_text:

            if len( self.extra_text ) == 1 \
                    and self.extra_text[0] == NO_GRAMMAR_CHANGES \
                    and self.stage.value != IntermediateGrammar.BEGINNING:

                return wrap_text( """%s%s\n#    %s
                    """ % ( self.name, self.stage, "\n#    ".join( self.extra_text ) ) )

            return wrap_text( """%s%s\n#    %s\n%s
                """ % ( self.name, self.stage, "\n#    ".join( self.extra_text ), self.grammar ) )

        return wrap_text( """%s%s\n%s
            """ % ( self.name, self.stage, self.grammar ) )

    def __eq__(self, other):
        """
            Determines whether this grammar history entry is equal or not to another one given.
        """

        if isinstance(self, other.__class__):

            if ( self.stage.value == self.MIDDLE or other.stage.value == self.MIDDLE or self.stage == other.stage ) \
                    and str( self.grammar ) == str( other.grammar ):
                return True

        return False

