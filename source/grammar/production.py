#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
from debug_tools import getLogger

from .symbols import Terminal
from .symbols import NonTerminal

from .utilities import get_unique_hash
from .lockable_type import LockableType

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, os.path.basename( os.path.dirname( os.path.abspath ( __file__ ) ) ) )


class Production(LockableType):
    """
        A full featured Chomsky Grammar production.
    """

    def __init__(self, sequence=0, symbols=[], lock=False):
        """
            Creates a new fresh production.

            `sequence` the index of the first symbol of the symbol's sequence
            `symbols` a list of initial symbols to add to the production
            `lock` if True, the object will be immediately locked upon creation
        """
        super().__init__()
        self.symbols = []

        if not isinstance( sequence, int ):
            raise RuntimeError( "The sequence parameter must to be an integer! %s" % sequence )

        self.sequence = sequence
        self.has_epsilon = False

        if symbols:

            for symbol in symbols:
                self.add( symbol )

        if lock:
            self.lock()

    def __setattr__(self, name, value):
        """
            Block attributes from being changed after it is activated.
            https://stackoverflow.com/questions/17020115/how-to-use-setattr-correctly-avoiding-infinite-recursion
        """

        if self.locked:
            raise AttributeError( "Attributes cannot be changed after `locked` is set to True! %s" % self.__repr__() )

        else:
            super().__setattr__( name, value )

    def __str__(self):
        """
            Return a nice string representation of this set.
        """
        symbols_str = []

        for symbol in self.symbols:
            symbols_str.append( str( symbol ) )

        return " ".join( symbols_str )

    def __lt__(self, other):
        """
            Operator less than used when comparing production's objects.
        """

        if isinstance( other, LockableType ):
            return str( self ) < str( other )

        raise TypeError( "'<' not supported between instances of '%s' and '%s'" % (
                self.__class__.__name__, other.__class__.__name__ ) )

    def __getitem__(self, key):
        """
            Called by Python automatically when indexing a production as in object[index].
        """
        return self.symbols[key]

    def __iter__(self):
        """
            Called by Python automatically when iterating over this set and python wants to start
            the iteration process.
        """
        self.__dict__['index'] = -1
        return self

    def __next__(self):
        """
            Return the next item immediate for the current iteration.
        """
        index = self.index + 1

        if index < len( self.symbols ):
            self.__dict__['index'] = index
            return self.symbols[index]

        raise StopIteration

    def peek_next(self, lookahead=1):
        """
            Inside a item iteration, allow to the next nth element given by `lookahead`. If the
            search goes past end or it is the last item, return None.
        """
        index = self.index + lookahead

        if index < len( self.symbols ):
            return self.symbols[index]

        return None

    def following_symbols(self):
        """
            Similar to `peek_next()` but get all the following symbols until the end of the
            production. Return an empty list when there are not remaining symbols.
        """
        index = self.index + 1
        remaining_count = len( self.symbols )
        following_symbols = []

        while index < remaining_count:
            following_symbols.append( self.symbols[index] )
            index += 1

        return following_symbols

    def add(self, symbol):
        """
            Add a new symbol to the production. If the last added symbol and the current are
            Terminal ones, the old terminal is going to be removed and merged into the new one.
        """

        if type( symbol ) not in ( Terminal, NonTerminal ):
            raise RuntimeError( "You can only add Terminal's and NonTerminal's in a Production object! %s" % symbol )

        # Epsilon symbols have length 0
        if len( symbol ) == 0:

            if self.has_epsilon:
                return

            else:
                self.has_epsilon = True

        if not self._merge_terminals( symbol ):
            self.sequence += 1

        symbol.sequence = self.sequence
        symbol.lock()
        self.symbols.append( symbol )

    def _merge_terminals(self, new_symbol):

        if type( new_symbol ) is Terminal:

            if len( self.symbols ):
                last_symbol = self.symbols[-1]

                if type( last_symbol ) is Terminal:
                    new_symbol.str = last_symbol.str + new_symbol.str
                    del self.symbols[-1]
                    return True

        return False

    def lock(self):
        """
            Block further changes to this object attributes and save its length for faster access.
        """

        if self.locked:
            return

        self.len = len( self )
        self._len = lambda : self.len

        self.check_consistency()
        super().lock()

    def _len(self):
        lengths = []

        for symbol in self.symbols:
            lengths.append( len( symbol ) )

        return sum( lengths )

    def check_consistency(self):
        """
            Assures the symbol has meaning, i.e., is not empty.
        """

        if not self.symbols:
            raise RuntimeError( "Invalid production creation! Production with no length: `%s` (%s)" % self.symbols, sequence )

    def get_terminals(self):
        """
            Get all Terminal's this symbol is composed by, on their respective sequence/ordering.
        """
        return self._get_symbols( Terminal )

    def get_non_terminals(self):
        """
            Get all NonTerminal's this symbol is composed by, on their respective sequence/ordering.
        """
        return self._get_symbols( NonTerminal )

    def is_last(self, symbol):
        """
            Checks whether the a given symbol is the last in a production.

            `production` is a list of Terminal's and NonTerminal's, and `symbol` is a NonTerminal.
            The last `production` element has its sequence number equal to the production's list
            size.
        """
        return symbol.sequence >= self.symbols[-1].sequence

    def _get_symbols(self, symbolType):
        symbols = []

        for symbol in self.symbols:

            if type( symbol ) is symbolType:
                symbols.append( symbol )

        return symbols

    @staticmethod
    def copy_productions_except_epsilon(source, destine):
        """
            Copy all productions from one productions set to another, except the epsilon_terminal.

            Return `True` when the item was added in the destine, `False` when is already exists on
            destine.
        """
        is_copied = False

        for production in source:

            if production != epsilon_production:

                if production not in destine:
                    destine.add( production )
                    is_copied = True

        return is_copied


# Standard/common symbols used
epsilon_terminal = Terminal( '&' )
epsilon_production = Production( symbols=[epsilon_terminal], lock=True )

end_of_string_terminal = Terminal( '$', lock=True )

