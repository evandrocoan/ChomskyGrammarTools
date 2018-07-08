#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# Licensing
#
# Chomsky Grammar Symbols Types
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

from .lockable_type import LockableType
from debug_tools import getLogger

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, __name__ )

HISTORY_KEY_LINE = "-- Grammar History"
NO_GRAMMAR_CHANGES = "No changes performed."


class ChomskyGrammarSymbol(LockableType):
    """
        General representation for a ChomskyGrammar symbol.

        After locking, its length representation is going to be saved as an attribute and returned
        when needed.
    """

    def __init__(self, symbols, sequence=0, lock=False):
        """
            A full featured Chomsky Grammar symbol able to compose a production or start symbol.

            `symbols` a string representing this symbol
            `sequence` is a integer representing the symbol sort order in a production.
            `lock` if True, the object will be immediately locked upon creation.
        """
        super().__init__()

        ## The string representation of this symbol
        self.str = str( symbols )
        self.check_consistency()

        ## The position of this symbol from the start of the production beginning at 1
        self.sequence = sequence

        ## Caches the length of this symbol, useful after its changes have been locked by `lock()`
        self.len = 0

        if lock:
            self.lock()

    def check_consistency(self):
        """
            Assures the symbol has meaning, i.e., is not empty.
        """

        if not self.str:
            raise RuntimeError( "Invalid symbol creation! Symbol with no length: `%s`" % self.str )

    def __lt__(self, other):
        """
            Operator less than `<` used when comparing production's objects.

            A symbol is compared explicitly by its string representation.
        """

        if isinstance( other, LockableType ):
            return str( self ) < str( other )

        raise TypeError( "'<' not supported between instances of '%s' and '%s'" % (
                self.__class__.__name__, other.__class__.__name__ ) )

    def _str(self):
        return self.str

    def lock(self):
        """
            Block further changes to this object attributes and save its length for faster access.
        """

        if self.locked:
            return

        self.trim_epsilons()
        self.check_consistency()
        super().lock()

    def trim_epsilons(self, new_copy=False):
        """
            Merges the epsilon symbol with other symbols, because the epsilon symbol has not
            meaning, unless it is alone.

            If `new_copy` is True, then instead of modifying the current object, return a new copy
            with epsilon's trimmed.
        """

        if new_copy:
            self = self.new()

        if len( self ):
            new_symbols = []

            for symbol in self.str:

                if symbol != '&':
                    new_symbols.append( symbol )

            self.str = "".join( new_symbols )

        else:
            self.str = self.str[0]


class Terminal(ChomskyGrammarSymbol):
    """
        Represents a terminal symbol on an ChomskyGrammar.
    """

    def _len(self):
        """
            Represents a terminal symbol on an ChomskyGrammar.
        """

        for symbol in self.str:

            if symbol != '&':
                return 1

        return 0


# Standard/common symbols used
epsilon_terminal = Terminal( '&' )
end_of_string_terminal = Terminal( '$', lock=True )


class NonTerminal(ChomskyGrammarSymbol):
    """
        Represents a non terminal symbol on an ChomskyGrammar.
    """
    def _len(self):
        return 1

    def check_consistency(self):
        """
            Assures the symbol has meaning, i.e., is not empty.
        """
        super().check_consistency()

        if not len( self ):
            raise RuntimeError( "Invalid symbol creation! Symbol with no length: `%s`" % self.str )

