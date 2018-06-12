#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from .lockable_type import LockableType

from debug_tools import getLogger

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, os.path.basename( os.path.dirname( os.path.abspath ( __file__ ) ) ) )

HISTORY_KEY_LINE = "-- Grammar History"


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
        self.str = str( symbols )

        self.check_consistency()
        self.sequence = sequence
        self.has_epsilon = False

        if lock:
            self.lock()

    def check_consistency(self):
        """
            Assures the symbol has meaning, i.e., is not empty.
        """

        if not self.str:
            raise RuntimeError( "Invalid symbol creation! Symbol with no length: `%s` (%s)" % self.str, sequence )

    def __lt__(self, other):

        if isinstance( other, LockableType ):
            return str( self ) < str( other )

        raise TypeError( "'<' not supported between instances of '%s' and '%s'" % (
                self.__class__.__name__, other.__class__.__name__ ) )

    def _len(self):
        length = len( self.str )

        for symbol in self.str:

            if symbol == '&':
                length -= 1
                self.has_epsilon = True

        return length

    def _str(self):
        return self.str

    def lock(self):
        """
            Block further changes to this object attributes and save its length for faster access.
        """

        if self.locked:
            return

        self.len = len( self )
        self._len = lambda : self.len

        self.trim_epsilons()
        self.check_consistency()
        super().lock()

    def trim_epsilons(self):
        """
            Merges the epsilon symbol with other symbols, because the epsilon symbol has not
            meaning, unless it is alone.
        """

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
    pass


class NonTerminal(ChomskyGrammarSymbol):
    """
        Represents a non terminal symbol on an ChomskyGrammar.
    """
    def _len(self):
        return 1

