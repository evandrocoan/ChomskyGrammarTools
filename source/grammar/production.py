#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

import copy
import itertools

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

    def __init__(self, symbols=[], lock=False):
        """
            Creates a new fresh production.

            `symbols` a list of initial symbols to add to the production
            `lock` if True, the object will be immediately locked upon creation
        """
        super().__init__()

        if isinstance( symbols, Production ):
            self._copy_construc( symbols )
            return

        else:
            ## A list of Terminal's and NonTerminal's this production is composed
            self.symbols = []

        ## The last symbols' sequence starting from 1
        self.sequence = 0

        ## Whether this production has some Epsilon symbol or not
        self.has_epsilon = False

        ## Caches the length of this symbol, useful after its changes have been locked by `lock()`
        self.len = 0
        self._original_len = self._len

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

        return "\n".join( symbols_str )

    def __lt__(self, other):
        """
            Operator less than `<` used when comparing production's objects.

            A symbol is compared explicitly by its string representation.
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

    def combinations(self, non_terminals_to_ignore=[]):
        """
            Return a new set within all its non terminal's removal combinations.

            How do use itertools in Python to build permutation or combination
            http://thomas-cokelaer.info/blog/2012/11/how-do-use-itertools-in-python-to-build-permutation-or-combination/
        """
        # log( 1, "self: %s", self )
        combinations = set([epsilon_terminal])

        non_terminals = self.get_non_terminals()
        non_terminals_count = len( non_terminals )

        for permutation_size in range( 1, non_terminals_count ):
            n_items_permutation = list( itertools.permutations( non_terminals, permutation_size ) )
            # log( 1, "permutation_size: %s", permutation_size )

            for permutation in n_items_permutation:
                new_production = self.new( True )
                new_production.filter_non_terminals( permutation, non_terminals_to_ignore )

                combinations.add( new_production )
                # log( 1, "new_production: %s", new_production )

        return combinations

    def filter_non_terminals(self, non_terminals_to_keep, non_terminals_to_ignore):
        """
            Removes all non terminal's not present on the  given list `non_terminals_to_keep`.
        """

        for symbol in self.symbols:

            if type( symbol ) is NonTerminal:

                if symbol not in non_terminals_to_keep and symbol not in non_terminals_to_ignore:
                    self.symbols[symbol.sequence - 1] = epsilon_terminal

        self.trim_epsilons()

    def remove_non_terminal(self, index):
        """
            Given an index starting from 0, removes the nth non terminal's.
        """
        terminal_index = -1

        for symbol in self.symbols:

            if type( symbol ) is NonTerminal:
                terminal_index += 1

                if terminal_index == index:
                    self.symbols[symbol.sequence - 1] = epsilon_terminal
                    break

    def trim_epsilons(self, new_copy=False):
        """
            Removes all meaningless epsilon's, i.e., with no meaning, useless.

            If `new_copy` is True, then instead of modifying the current object, return a new copy
            with epsilon's trimmed.
        """
        new_symbols = []

        if new_copy:
            self = self.new( True )

        for symbol in self.symbols:

            if len( symbol ):
                new_symbols.append( symbol )

        if not len( new_symbols ):
            new_symbols.append( epsilon_terminal )

        self.symbols = new_symbols
        self.lock()
        return self

    def new(self, unlocked=False):
        """
            Creates and return a new copy of the current a object.
        """
        new_copy = copy.deepcopy( self )

        if unlocked:
            new_copy.unlock()

        else:
            new_copy.lock()

        return new_copy

    def _copy_construc(self, other):
        """
            Is there a decent way of creating a copy constructor in python?
            https://stackoverflow.com/questions/10640642/is-there-a-decent-way-of-creating-a-copy-constructor-in-python
        """
        self.__dict__ = other.__dict__.deepcopy()

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

    def unlock(self):
        self.__dict__['locked'] = False
        self._len = self._original_len

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

