#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# Licensing
#
# Chomsky Grammar Productions
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

import copy
import itertools

from debug_tools import getLogger
from debug_tools.lockable_type import LockableType

from .symbols import Terminal
from .symbols import NonTerminal

from .symbols import epsilon_terminal
from .symbols import end_of_string_terminal

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, __name__ )


class Production(LockableType):
    """
        A full featured Chomsky Grammar production.
    """

    def __init__(self, symbols=None, lock=False):
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

    def __repr__(self):
        """
            Return a more complete and precise string representation of this object, useful for
            debugging purposes. But requires the `USE_STRING` constant to be set to False.
        """

        if self.USE_STRING:
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

    def  __setitem__(self, key, element):
        """
            Called by Python automatically when indexing a production as in object[index].
        """
        self.symbols[key] = element

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

    def combinations(self, non_terminal_epsilon):
        """
            Return a new set within all its non terminal's removal combinations, accordingly with
            the non terminal's set on `non_terminal_epsilon`.

            How do use itertools in Python to build permutation or combination
            http://thomas-cokelaer.info/blog/2012/11/how-do-use-itertools-in-python-to-build-permutation-or-combination/
        """
        # log( 1, "self: %s", self )
        combinations = set()

        non_terminals = self.non_terminals( position=True )
        non_terminals_count = len( non_terminals )

        for permutation_size in range( 0, non_terminals_count ):
            n_items_permutation = list( itertools.permutations( non_terminals, permutation_size ) )
            # log( 1, "permutation_size: %s, n_items_permutation: %s", permutation_size, n_items_permutation )

            for permutation in n_items_permutation:
                new_production = self.new()

                try:
                    new_production.filter_non_terminals( non_terminal_epsilon, permutation )

                except RuntimeError as error:

                    if str( error ).startswith( "Invalid production creation! Production with no length: [&]" ):
                        new_production = epsilon_production.new()

                    else:
                        raise

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

                if symbol in non_terminal_epsilon and (symbol, symbol.sequence) not in non_terminals_to_keep:
                    self.symbols[symbol.sequence - 1] = epsilon_terminal

        if not len( self ):
            self.add( epsilon_terminal.new() )

        self.trim_epsilons()
        self.lock()
        # log( 1, "self: \n%s", self )

    def remove_everything_after(self, index):
        """
            Given an index starting from 0 nth, removes all the symbols after it, excluding the 0 nth symbol.
        """
        self.trim_epsilons()
        self.symbols = self.symbols[:index+1]

    def remove_everything_before(self, index):
        """
            Given an index starting from 0 nth, removes all the symbols before it excluding 0 nth symbol.
        """
        self.trim_epsilons()
        self.symbols = self.symbols[index:]

    def remove(self, index):
        """
            Given an index starting from 0, removes the nth symbol's, either Terminal or NonTerminal.
        """
        self.symbols[index] = epsilon_terminal

    def remove_terminal(self, index):
        """
            Given an index starting from 0, removes the nth terminal's.
        """
        self._remove_nth_symbol( index, Terminal )

    def remove_non_terminal(self, index):
        """
            Given an index starting from 0, removes the nth non terminal's.
        """
        self._remove_nth_symbol( index, NonTerminal )

    def _remove_nth_symbol(self, index, symbol_type):
        """
            Given an index starting from 0, removes the nth symbol with type `symbol_type`.
        """
        symbol_index = -1

        for symbol in self.symbols:

            if type( symbol ) is symbol_type:
                symbol_index += 1

                if symbol_index == index:
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
            Inside a item iteration, allow to look the next nth element given by `lookahead`. If the
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
        self = self.new()
        self.remove_everything_before( self._index + 1 )
        self.lock()
        return self

    def add(self, symbol):
        """
            Add a new symbol to the production. If the last added symbol and the current are
            Terminal ones, the old terminal is going to be removed and merged into the new one.
        """
        # log( 1, "symbol: %s", symbol )

        if type( symbol ) not in ( Terminal, NonTerminal ):
            raise RuntimeError( "You can only add Terminal's and NonTerminal's! %s (%s)" % ( symbol.repr(), type( symbol ) ) )

        if symbol.locked:
            raise RuntimeError( "You can only add `unlocked` symbols in a production! %s" % symbol.repr() )

        self.sequence += 1
        symbol.sequence = self.sequence
        symbol.lock()

        self.symbols.append( symbol )
        # log( 1, "self.symbols: %s (%s)", self.symbols, type( self.symbols ) )

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

    def terminals(self, index=-1):
        """
            Get all Terminal's this symbol is composed by, on their respective sequence/ordering.

            If `index` is provided greater than `-1`, instead of returning a list, return the list
            nth element. If the `index` is out of range, then an empty set will be returned.
        """
        return self._get_symbols( Terminal, index )

    def non_terminals(self, index=-1, position=False):
        """
            Get all NonTerminal's this symbol is composed by, on their respective sequence/ordering.

            If `index` is provided greater than `-1`, instead of returning a list, return the list
            nth element. If the `index` is out of range, then an empty set will be returned.

            If `position`, list with tuples with (symbol, position) in the production.
        """
        return self._get_symbols( NonTerminal, index, position )

    def _get_symbols(self, symbol_type, index=-1, position=False):
        symbols = []

        for symbol in self.symbols:

            if type( symbol ) is symbol_type:

                if position:
                    symbols.append( ( symbol, symbol.sequence ) )

                else:
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
            Copy all productions from one productions set to another, except the `epsilon_production`.

            Return `True` when the item was added in the destine, `False` when is already exists on destine.
        """
        old_length = len( destine )

        for production in source:

            if production != epsilon_production:
                destine.add( production )

        return old_length != len( destine )


# Standard/common symbols used
epsilon_production = Production( symbols=[epsilon_terminal], lock=True )

