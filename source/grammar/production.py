#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

import copy
import itertools

from debug_tools import getLogger

from .symbols import Terminal
from .symbols import NonTerminal

from .lockable_type import LockableType

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, __name__ )


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

        ## Caches the length of this symbol, useful after its changes have been locked by `lock()`
        self.len = 0

        if symbols:

            for symbol in symbols:
                self.add( symbol )

        # log( 1, "symbols: %s", symbols )
        if lock:
            self.lock()

    def __setattr__(self, name, value):
        """
            Block attributes from being changed after it is activated.
            https://stackoverflow.com/questions/17020115/how-to-use-setattr-correctly-avoiding-infinite-recursion
        """

        if self.locked:
            raise AttributeError( "Attributes cannot be changed after `locked` is set to True! %s" % self )

        else:
            super().__setattr__( name, value )

    def __repr__(self):

        if self._USE_STRING:
            return super().__repr__()

        return super().__repr__() + '\n'

    def __str__(self):
        """
            Return a nice string representation of this set.
        """
        symbols_str = []
        # log( 1, "self.symbols: %s", self.symbols )

        for symbol in self.symbols:
            symbols_str.append( str( symbol ) )

        return " ".join( symbols_str )

    def _len(self):
        lengths = []

        for symbol in self.symbols:
            lengths.append( len( symbol ) )

        return sum( lengths )

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

            `self._index` internally controls the which one is the current item in an iteration over
            an production
        """
        self.__dict__['_index'] = -1
        return self

    def __next__(self):
        """
            Return the next item immediate for the current iteration.
        """
        index = self._index + 1

        if index < len( self.symbols ):
            self.__dict__['_index'] = index
            return self.symbols[index]

        raise StopIteration

    def combinations(self, non_terminal_epsilon=[]):
        """
            Return a new set within all its non terminal's removal combinations, accordingly with
            the non terminal's set on `non_terminal_epsilon`.

            How do use itertools in Python to build permutation or combination
            http://thomas-cokelaer.info/blog/2012/11/how-do-use-itertools-in-python-to-build-permutation-or-combination/
        """
        # log( 1, "self: %s", self )
        combinations = set()

        non_terminals = self.get_non_terminals()
        non_terminals_count = len( non_terminals )

        for permutation_size in range( 0, non_terminals_count ):
            # log( 1, "permutation_size: %s", permutation_size )
            n_items_permutation = list( itertools.permutations( non_terminals, permutation_size ) )

            for permutation in n_items_permutation:
                new_production = self.new()

                try:
                    new_production.filter_non_terminals( non_terminal_epsilon, permutation )

                except RuntimeError as error:
                    error = str( error )

                    if error.startswith( "Invalid production creation! Production with no length: [&]" ):
                        new_production = epsilon_production.new()

                    else:
                        raise RuntimeError( error )

                # log( 1, "new_production: %s (%s)", new_production, repr( new_production ) )
                combinations.add( new_production )

        # log( 1, "combinations: \n%s", combinations )
        return combinations

    def filter_non_terminals(self, non_terminal_epsilon, non_terminals_to_keep):
        """
            Removes all non terminal's in the list `non_terminal_epsilon`, except the ones inside
            the list `non_terminals_to_keep`.
        """
        # log( 1, "non_terminal_epsilon: %s, non_terminals_to_keep: %s", non_terminal_epsilon, non_terminals_to_keep )

        for symbol in self.symbols:

            if type( symbol ) is NonTerminal:

                if symbol in non_terminal_epsilon and symbol not in non_terminals_to_keep:
                    self.symbols[symbol.sequence - 1] = epsilon_terminal

        if not len( self ):
            self.add( epsilon_terminal.new() )

        self.trim_epsilons()
        self.lock()
        # log( 1, "self: \n%s", self )

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

    def replace(self, target_index, new_production):
        """
            Given an `target_index` starting from 0, replace the nth symbol with the given
            `new_production` symbols.
        """
        self = self.new()
        old_symbols = self.symbols

        self.symbols = []
        self.sequence = 0

        for index, old_symbol in enumerate( old_symbols ):
            # log( 1, "old_symbol: %s, len: %s", old_symbol, len( old_symbol ) )

            if index == target_index:

                for symbol in new_production:
                    self.add( symbol.new() )

                continue

            self.add( old_symbol.new() )

        self.trim_epsilons()
        return self

    def trim_epsilons(self, new_copy=False):
        """
            Removes all meaningless epsilon's, i.e., with no meaning, useless.

            If `new_copy` is True, then instead of modifying the current object, return a new copy
            with epsilon's trimmed.
        """

        if new_copy:
            self = self.new()

        old_symbols = self.symbols
        self.symbols = []
        self.sequence = 0

        for old_symbol in old_symbols:
            # log( 1, "old_symbol: %s, len: %s", old_symbol, len( old_symbol ) )

            if len( old_symbol ):
                self.add( old_symbol.new() )

        if not len( self ):
            new_epsilon = epsilon_terminal.new()

            # log( 1, "new_epsilon: %s", new_epsilon )
            self.add( new_epsilon )

        return self

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
        index = self._index + lookahead

        if index < len( self.symbols ):
            return self.symbols[index]

        return None

    def following_symbols(self):
        """
            Similar to `peek_next()` but get all the following symbols until the end of the
            production. Return an empty list when there are not remaining symbols.
        """
        index = self._index + 1
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
        # log( 1, "symbol: %s", symbol )

        if type( symbol ) not in ( Terminal, NonTerminal ):
            raise RuntimeError( "You can only add Terminal's and NonTerminal's! %s (%s)" % ( symbol, type( symbol ) ) )

        if symbol.locked:
            raise RuntimeError( "You can only add `unlocked` symbols in a production! %s" % symbol )

        if not self._merge_terminals( symbol ):
            self.sequence += 1

        symbol.sequence = self.sequence
        symbol.lock()

        self.symbols.append( symbol )
        # log( 1, "self.symbols: %s (%s)", self.symbols, type( self.symbols ) )

    def _merge_terminals(self, new_symbol):
        """
            Return `True` when it is not required to increment the `sequence` counting, as the
            symbol was squashed with the last one.
        """

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
            Call `trim_epsilons()`, `check_consistency()` and its super class `lock()` to block
            further changes to this object attributes.
        """

        if self.locked:
            return

        self.trim_epsilons()
        self.check_consistency()
        super().lock()

    def check_consistency(self):
        """
            Assures the symbol has meaning, i.e., is not empty.
        """

        if not self.symbols:
            raise RuntimeError( "Invalid production creation! Production with no length: `%s`" % self.symbols )

    def get_terminals(self, index=-1):
        """
            Get all Terminal's this symbol is composed by, on their respective sequence/ordering.

            If `index` is provided greater than `-1`, instead of returning a list, return the list
            nth element. If the `index` is out of range, then an empty set will be returned.
        """
        return self._get_symbols( Terminal, index )

    def get_non_terminals(self, index=-1):
        """
            Get all NonTerminal's this symbol is composed by, on their respective sequence/ordering.

            If `index` is provided greater than `-1`, instead of returning a list, return the list
            nth element. If the `index` is out of range, then an empty set will be returned.
        """
        return self._get_symbols( NonTerminal, index )

    def _get_symbols(self, symbolType, index=-1):
        symbols = []

        for symbol in self.symbols:

            if type( symbol ) is symbolType:
                symbols.append( symbol )

        if index > -1:

            if index < len( symbols ):
                return symbols[index]

            else:
                return set()

        return symbols

    def is_last(self, symbol):
        """
            Checks whether the a given symbol is the last in a production.

            `production` is a list of Terminal's and NonTerminal's, and `symbol` is a NonTerminal.
            The last `production` element has its sequence number equal to the production's list
            size.
        """
        return symbol.sequence >= self.symbols[-1].sequence

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

