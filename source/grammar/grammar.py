#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# Licensing
#
# Chomsky Grammar
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
import re

from threading import Lock
from debug_tools import getLogger

import lark
from typing import Dict, Set

from .symbols import Terminal
from .symbols import NonTerminal
from .symbols import epsilon_terminal
from .symbols import HISTORY_KEY_LINE

from .production import Production
from .production import epsilon_production
from .production import end_of_string_terminal

from .utilities import IntermediateGrammar

from .utilities import getCleanSpaces
from .utilities import dictionary_to_string
from .utilities import convert_to_text_lines
from .utilities import get_duplicated_elements
from .utilities import sort_alphabetically_and_by_length

from .dynamic_iteration import DynamicIterationDict
from .tree_transformer import ChomskyGrammarTreeTransformer

# level 2 - Add and remove productions
# level 4 - Abstract Syntax Tree Parsing
# level 8 - Log addition and removal of productions
# level 16 - Factoring logging
# level 32 - Left Recursion elimination logging
log = getLogger( 127-2-4-8-16-32, __name__ )
log( 1, "Importing " + __name__ )


class ChomskyGrammar():
    """
        Chomsky Regular grammar.

        Example grammar:
        S -> aA | bB | a | b | &
        A -> aA | a
        B -> bB | b
    """

    _parser = lark.Lark( r"""
        productions   : new_line* ( space* non_terminal_start space* "->" space* non_terminals space* end_symbol )* space* non_terminal_start space* "->" space* non_terminals space* end_symbol?
        non_terminals : production ( "|" production )*
        production    : space* ( ( epsilon | terminal | non_terminal )+ space+ )* ( epsilon | terminal | non_terminal )+ space*

        // Forces them to appear in the tree as branches
        epsilon         : [] | "&"+
        end_symbol      : ";"* space* new_line ( new_line | space )*
        terminal        : ( DIGIT | LCASE_LETTER | signs | parens )+
        non_terminal    : UCASE_LETTER+ ( UCASE_LETTER | DIGIT | quote )*
        new_line        : NEWLINE
        quote           : "'"
        space           : " "

        // Tells the tree-builder to inline this branch if it has only one member
        ?signs    : minus |  plus | star | comma | colon | equals | semicolon | slash | backslash | dot
        semicolon : ";"
        comma     : ","
        colon     : ":"
        dot       : "."
        equals    : "="
        minus     : "-"
        star      : "*"
        plus      : "+"
        slash     : "/"
        backslash : "\\"

        ?parens       : open_paren | close_paren | open_bracket | close_bracket | open_brace | close_brace
        open_bracket  : "["
        close_bracket : "]"
        open_brace    : "{"
        close_brace   : "}"
        open_paren    : "("
        close_paren   : ")"

        // Rename the start symbol, so when parsing the tree it is simple to find it
        non_terminal_start : non_terminal

        // Tells the tree-builder to inline this branch if it has only one member
        ?non_terminal_epsilon : non_terminal | epsilon

        // Stops Lark from automatically filtering out these literals from the tree
        null   : "null"
        true   : "true"
        false  : "false"

        // Import common definitions
        %import common.INT
        %import common.DIGIT
        %import common.UCASE_LETTER
        %import common.LCASE_LETTER
        %import common.SIGNED_NUMBER
        %import common.NEWLINE
        %import common.WS_INLINE

        // Set to ignore white spaces
        // %ignore WS_INLINE
    """, start='productions' )

    @classmethod
    def parse(cls, inputGrammar):
        """
            Parse the regular grammar and return its Abstract Syntax Tree.
        """
        return cls._parser.parse( inputGrammar )

    def __str__(self):
        """
            Returns a formatted Automata Transition Table formatted as:
                 Q0' -> &    | a Q1 | b Q2
                 Q0  -> a Q1 | b Q2
                 Q1  -> b    | b Q0
                 Q2  -> a    | a Q0
        """
        grammar_lines = []
        biggest = self._get_table_biggest_elements()

        def create_grammar_line(start_symbol, productions):
            productions_string = []

            for production in productions:
                productions_string.append( str( production ) )

            log( 4, "productions:        %s", productions )
            log( 4, "productions_string: %s", productions_string )

            return " {:>{biggest}} -> {}".format( str( start_symbol ),
                    " | ".join( sort_alphabetically_and_by_length( productions_string ) ), biggest=biggest )

        if self.initial_symbol in self.productions:
            grammar_lines.append( create_grammar_line( self.initial_symbol, self.productions[self.initial_symbol] ) )

        else:
            raise RuntimeError( "Your grammar has an invalid initial_symbol! %s, %s" % ( self.initial_symbol, self.productions ) )

        for non_terminal in sort_alphabetically_and_by_length( set( self.productions ) - {self.initial_symbol} ):
            grammar_lines.append( create_grammar_line( non_terminal, self.productions[non_terminal] ) )

        return "\n".join( grammar_lines )

    def _get_table_biggest_elements(self):
        biggest_label_length = 0

        for production in self.productions:
            production_length = len( str( production ) )

            if production_length > biggest_label_length:
                biggest_label_length = production_length

        log( 4, "biggest_label_length: %s", biggest_label_length )
        return biggest_label_length

    def initial_symbol_as_first(self):
        """
            Return a lists with all start symbols, but with the grammar initial symbol as first and
            the following symbols in sorted accordingly to `sort_alphabetically_and_by_length()`
            function. See that function documentation for the sorting order.
        """
        initial_symbol = self.initial_symbol
        production_keys = sort_alphabetically_and_by_length( list( set( self.productions ) - {initial_symbol} ) )
        production_keys.insert( 0, initial_symbol )
        return production_keys

    def __init__(self):
        """
            Create a new grammar.
        """
        self._initial_symbol = ""

        ## A dictionary with productions this grammar can generates
        self.productions = DynamicIterationDict()

        ## Saves all grammars operations history
        self.operations_history = []

        ## Saves the last step count used to factoring a grammar by the `factor_it()` method
        self.last_factoring_step = 0

        # https://stackoverflow.com/questions/13119066/documenting-a-non-existing-member-with-doxygen
        if None:
            ## initial_symbol the initial symbol of this grammar
            self.initial_symbol = None

    def _save_history(self, operation_name, operation_stage=IntermediateGrammar.MIDDLE):
        intermediateGrammar = IntermediateGrammar( self, operation_name, operation_stage )

        if len( self.operations_history ) and intermediateGrammar == self.operations_history[-1]:
            return

        self.operations_history.append( IntermediateGrammar( self, operation_name, operation_stage ) )

    def _save_data(self, text_data, *arguments):

        if arguments:

            for argument in arguments:

                if argument:
                    self.operations_history[-1].extra_text.append( text_data % arguments )
                    break

    def get_operation_history(self):
        """
            Return a string with all operations' history for this grammar.
        """
        counter = 0
        history_list = []
        operations_history = self.operations_history

        for index, operation in enumerate( self.operations_history ):
            stage = operation.stage.value

            if stage == IntermediateGrammar.BEGINNING:

                if len( history_list ):
                    extra_text = operation.extra_text

                    if extra_text:
                        # https://stackoverflow.com/questions/8785554/how-do-i-insert-a-list-at-the-front-of-another-list
                        operations_history[index+1].extra_text[0:0] = extra_text

                    continue

            if stage == IntermediateGrammar.END:

                if not operation.extra_text:
                    operation.extra_text.append( "No changes required/performed here." )

            counter += 1
            history_list.append( "# %s. %s" % ( counter, operation ) )

        return "\n\n".join( history_list )

    @property
    def initial_symbol(self):
        """
            Returns the current initial symbol.
        """
        return self._initial_symbol

    @initial_symbol.setter
    def initial_symbol(self, value):
        """
            Set the initial symbol assuring it has the minimum requirements.
        """
        self.assure_correct_start_symbol( value )
        self._initial_symbol = value

    def assure_correct_start_symbol(self, start_symbol):
        """
            Checks whether a given `start_symbol` has the required properties to be a valid start symbol.

            If it is an invalid start symbol Production, an RuntimeError will be threw.
        """

        if type( start_symbol ) is not Production:
            raise RuntimeError( "Your start symbol is not an instance of Production! %s (%s)" % ( start_symbol, repr( start_symbol ) ) )

        if len( start_symbol ) != 1:
            raise ValueError( "The start symbol be a Production with length 1! %s (%s)" % ( start_symbol, repr( value ) ) )

        if type( start_symbol[0] ) is not NonTerminal:
            raise ValueError( "The start symbol production first symbol must be a NonTerminal! %s (%s)" % ( start_symbol, repr( value ) ) )

        start_symbol.lock()

    def __len__(self):
        """
            Returns the length of this grammar as being the counting of productions start symbols it
            has.
        """
        return len( self.productions )

    @classmethod
    def load_from_text_lines(cls, input_text_form):
        """
            Returns a regular grammar that generates the language of the given it on the text form
            as:
                1 -> a | a2 | b | b2
                2 -> a | a2 | b | b2
        """
        AST = cls.parse( "\n".join( getCleanSpaces( input_text_form, lineCutTrigger=HISTORY_KEY_LINE, keepSpaceSepators=True ) ) )
        grammar = ChomskyGrammar()

        # initial_symbol: 1
        # productions:    {'1': {'b', 'a2', 'b2', 'a'}, '2': {'b', 'a2', 'b2', 'a'}}
        log( 4, "\n%s", AST.pretty() )

        # S -> S SS | &
        current_level = ''

        def parse_tree(tree, level, children_count):
            level_name = tree.data

            nonlocal grammar
            nonlocal current_level

            for node in tree.children:

                if isinstance( node, lark.Tree ):
                    log( 4, "level: %s, level_name: %-15s children_count: %s", level, level_name, children_count )
                    parse_tree( node, level+1, len( node.children ) )

                else:
                    log( 4, "level: %s, level_name: %-15s node: %-15s current_level: %s", level, level_name, node, current_level )

                    if level_name == 'productions':

                        if level == 0:
                            current_level = node

                            if len( grammar.initial_symbol ) == 0:
                                log( 4, "setting initial_symbol: %s", grammar.initial_symbol )
                                grammar.initial_symbol = current_level

                    if level_name == 'non_terminals':
                        grammar.add_production( current_level, node )

        new_tree = ChomskyGrammarTreeTransformer().transform( AST )
        parse_tree( new_tree, 0, len( new_tree.children ) )

        log( 4, "\n%s", new_tree.pretty() )
        log( 4, "Result initial_symbol: %s", grammar.initial_symbol )
        log( 4, "Result productions:    %s", grammar.productions )
        log( 4, "Result grammar:        %s", grammar )
        grammar.assure_existing_symbols()
        return grammar

    def add_production(self, start_symbol, production):
        """
            Add a new `production` to this grammar given a `start_symbol`.

            The production object is a composition of several Terminal's and NonTerminal's symbols.
        """
        self.assure_correct_start_symbol( start_symbol )

        if type( production ) is not Production:
            raise RuntimeError( "Your production is not an instance of Production! %s -> %s" % ( start_symbol, production ) )

        production.lock()

        if start_symbol not in self.productions:
            self.productions[start_symbol] = DynamicIterationDict()

        log( 58, "   %s -> %s", start_symbol, production )
        self.productions[start_symbol].add( production )

    def has_production(self, start_symbol, production):
        """
            Returns True if the `start_symbol` has the given `production`.
        """
        return production in self.productions[start_symbol]

    def terminals_productions(self, start_symbol):
        """
            Given the non terminal `start_symbol`, return all reachable productions only composed
            with terminal's.
        """
        productions = self.productions[start_symbol]
        reachable_terminals = set()

        for production in productions:
            only_terminals = True

            for symbol in production:

                if type( symbol ) is NonTerminal:
                    only_terminals = False
                    break

            if only_terminals:
                reachable_terminals.add( production )

        return reachable_terminals

    def non_terminals(self, start_symbol):
        """
            Given a `start_symbol` as S, return all its non terminal's reachable from it, with or
            without terminal's together.
        """
        return self.symbols_composition( self.productions[start_symbol], NonTerminal )

    def terminals(self, symbol):
        """
            Given a `start_symbol` as S, return all its terminal's reachable from it, with or
            without non terminal's together.
        """
        return self.symbols_composition( self.productions[symbol], Terminal )

    @staticmethod
    def symbols_composition(productions, symbolType):
        """
            For each production in `productions`, get all symbol of type `symbolType` they are composed.
        """
        symbols_composition = set()

        for production in productions:
            symbols = production._get_symbols( symbolType )
            symbols_composition.update( symbols )

        return symbols_composition

    def assure_existing_symbols(self):
        """
            Checks whether the grammar uses non existent non terminal symbols as `S -> Aa | a` or if
            there is a empty start symbol `S ->`.
        """
        production_keys = self.productions
        start_non_terminals = self.symbols_composition( production_keys, NonTerminal )

        for start_symbol in production_keys:
            non_terminals = self.non_terminals( start_symbol )

            for non_terminal in non_terminals:

                if non_terminal not in start_non_terminals:
                    raise RuntimeError( "Invalid Non Terminal `%s` added to the grammar: \n%s" % ( non_terminal, self ) )

        if self.initial_symbol not in production_keys:
            raise ValueError( "Error: The new initial symbol has not productions! %s" % repr( self.initial_symbol ) )

    def is_epsilon_free(self):
        """
            Return `True` if the start symbol is recursive and has epsilon transitions or if other
            non initial symbol start non terminal have epsilon.
        """

        for non_terminal in self.productions:

            if self.has_production( non_terminal, epsilon_production ):

                if non_terminal == self.initial_symbol:

                    if self.has_recursion_on_the_non_terminal( non_terminal ):
                        return False

                else:
                    return False

        return True

    def has_recursion_on_the_non_terminal(self, non_terminal_to_check):
        """
            Return `True` if the given `non_terminal_to_check` is recursive with himself.
        """
        recursive_terminals = DynamicIterationDict([non_terminal_to_check])

        for non_terminal in recursive_terminals:
            productions = self.productions[non_terminal]

            for production in productions:
                # log( 1, "production: %s", production )

                for symbol in production:
                    # log( 1, "symbol: %s", symbol )

                    if type( symbol ) is NonTerminal:

                        if symbol == non_terminal_to_check:
                            # log( 1, "recursive_terminals: %s", recursive_terminals )
                            return True

                        if symbol not in recursive_terminals:
                            recursive_terminals.add( symbol )

        # log( 1, "recursive_terminals: %s", recursive_terminals )
        return False

    def non_terminal_epsilon(self):
        """
            Creates the non terminal's epsilon set, within all non terminal's which lead to epsilon
            with 0 or more transitions.
        """
        old_counter = -1
        current_counter = 0

        production_keys = self.productions
        non_terminal_epsilon = DynamicIterationDict()

        for start_symbol in production_keys:

            if self.has_production( start_symbol, epsilon_production ):
                non_terminal_epsilon.add( start_symbol )

        while current_counter != old_counter:
            old_counter = current_counter

            for start_symbol in production_keys:
                productions = production_keys[start_symbol]

                for production in productions:
                    # log( 1, "production: %s", production )
                    all_symbols_go_to_epsilon = False

                    for symbol in production:
                        # log( 1, "symbol: %s", symbol )

                        if type( symbol ) is NonTerminal:

                            if symbol in non_terminal_epsilon:
                                all_symbols_go_to_epsilon = True
                                continue

                        all_symbols_go_to_epsilon = False
                        break

                    if all_symbols_go_to_epsilon and start_symbol not in non_terminal_epsilon:
                        non_terminal_epsilon.add( start_symbol )
                        current_counter += 1

        # log( 1, "non_terminal_epsilon: %s", non_terminal_epsilon )
        return non_terminal_epsilon

    def convert_to_epsilon_free(self):
        """
            Convert the current grammar to a epsilon free grammar.
        """
        # log( 1, "self: \n%s", self )
        self._save_history( "Converting to Epsilon Free", IntermediateGrammar.BEGINNING )

        initial_symbol = self.initial_symbol
        production_keys = self.productions
        non_terminal_epsilon = self.non_terminal_epsilon()

        for start_symbol in production_keys:
            start_production = production_keys[start_symbol]

            for production in start_production(1):

                for combination in production.combinations( non_terminal_epsilon ):
                    # log( 1, "combination: %s", combination )
                    self.add_production( start_symbol, combination )

            self.remove_production( start_symbol, epsilon_production )

        if initial_symbol in non_terminal_epsilon:

            if self.has_recursion_on_the_non_terminal( initial_symbol ):
                new_initial_symbol = self.new_symbol()
                self.copy_productions_for_one_non_terminal( initial_symbol, new_initial_symbol )
                self.initial_symbol = new_initial_symbol

            self.add_production( self.initial_symbol, epsilon_production )

        self._save_history( "Converting to Epsilon Free", IntermediateGrammar.END )
        self._save_data( "Non Terminal's Deriving Epsilon: %s", "; ".join( "%s -> &" % ( key )
               for key, element in non_terminal_epsilon.items() ) )

    def remove_production(self, start_symbol, production, recursive=True):
        """
            Given a `start_symbol` remove its `production`.

            If `recursive` is True and the removed production was the last production, then the
            `start_symbol` symbol is also removed from the grammar `productions` and everywhere it
            is mentioned.
        """
        log( 58, "%s -> %s", start_symbol, production )
        productions = self.productions[start_symbol]
        productions.discard( production )

        if recursive and not productions:
            self.remove_start_non_terminal( start_symbol )

    def remove_start_non_terminal(self, start_non_terminal, recursive=True):
        """
            Given a `start_non_terminal` remove it from the grammar and all productions which points to it.

            If `start_non_terminal` is a initial symbol, `clean_initial_symbol()` will also be called.

            If `recursive` is True the `start_non_terminal` symbol will be removed everywhere it is mentioned.
        """
        production_keys = self.productions

        if recursive:

            for start_symbol in production_keys(1):
                # Do remove the productions from itself, because:
                # 1. There is no need for it as everything is going to be removed anyway
                # 2. It can cause a recursion with `remove_production()` which also call
                #    `remove_start_non_terminal()` when all productions are removed from `start_symbol`
                if start_symbol == start_non_terminal:
                    continue

                start_productions = production_keys[start_symbol]

                for production in start_productions:

                    for symbol in production:

                        if symbol == start_non_terminal:
                            self.remove_production( start_symbol, production )
                            break

        del production_keys[start_non_terminal]
        self.clean_initial_symbol( start_non_terminal )

    def clean_initial_symbol(self, start_symbol):
        """
            Replace the current initial symbol creating a new empty initial symbol such `S -> S` by
            querying `new_symbol()` for a new initial symbol.

            Return True when the initial symbol was removed.
        """

        if self.initial_symbol == start_symbol:
            # log( 1, "WARNING: Removing the grammar initial symbol!" )
            new_initial_symbol = self.new_symbol()
            self.add_production( new_initial_symbol, new_initial_symbol )

            self.initial_symbol = new_initial_symbol
            return True

        return False

    def copy_productions_for_one_non_terminal(self, non_terminal_source, non_terminal_destine, secondGrammar=None):
        """
            Given one start production `non_terminal_source` and a `non_terminal_destine`, copy all
            productions from the source symbol to the destine symbol.

            If a `secondGrammar` is given, copy the symbols from the source at the current grammar
            to the destine at the `secondGrammar`.
        """

        if secondGrammar:
            secondGrammarProductions = secondGrammar.productions[non_terminal_source]

        else:
            secondGrammarProductions = self.productions[non_terminal_source]

            if non_terminal_source == non_terminal_destine:
                return

        for production in secondGrammarProductions:
            self.add_production( non_terminal_destine, production )

    def new_symbol(self, new_symbol='S', use_digits=False):
        """
            Given a `new_symbol` initial name, search for a new symbol name until find one in the
            form S'''... and returns it.

            If `use_digits` is passed as True, then use numbers to represent the new symbols instead
            of single quotes `'`.
        """
        new_symbol = str( new_symbol )

        if not new_symbol:
            raise RuntimeError( "The new_symbol `%s` has not length! (%s)\n%s" % ( new_symbol, repr( new_symbol ), self ) )

        clean_symbol = new_symbol
        production_keys = self.productions

        if use_digits:
            current_counter = 0
            search_result = re.findall( r'\d+', new_symbol )

            if search_result:
                current_counter = int( search_result[-1] )
                search_result = re.findall( r'[^\d]+', new_symbol )

                if search_result:
                    clean_symbol = search_result[-1]

            def push_next_symbol():
                nonlocal current_counter
                current_counter += 1

        else:
            current_counter = ""

            def push_next_symbol():
                nonlocal current_counter
                current_counter += "'"

        while True:
            push_next_symbol()
            new_symbol = NonTerminal( clean_symbol + str( current_counter ), lock=True )

            if new_symbol not in production_keys:
                return Production( symbols=[new_symbol.new()], lock=True )

    def left_recursion(self):
        """
            Returns a set with tuples (non terminal, recursion_type) where `non terminal` is a
            grammar recursive non terminal and `recursion_type` the type of the recursion which
            can be 'direct' or 'indirect'.
        """
        left_recursion = set()
        production_keys = self.productions
        first_non_terminals = self.first_non_terminals()

        for first in first_non_terminals.keys():

            if first in first_non_terminals[first]:
                is_direct = False

                for production in production_keys[first]:

                    if production[0] == first:
                        is_direct = True
                        break

                if is_direct:
                    left_recursion.add( ( first, 'direct' ) )

                else:
                    left_recursion.add( ( first, 'indirect' ) )

        return left_recursion

    def has_left_recursion(self):
        """
            Determines whether this grammar has left recursion on any of its start non terminal's
            symbols.
        """
        return bool( self.left_recursion() )

    def eliminate_left_recursion(self):
        """
            Eliminates direct or indirect left recursion from this grammar.

            The indirect recursion elimination order is defined by the `initial_symbol_as_first()`
            function. See that function documentation for the sorting order.
        """
        self._save_history( "Eliminating Left Recursion", IntermediateGrammar.BEGINNING )

        if self.has_left_recursion():
            self.convert_to_proper()
            log( 32, "self: \n%s", self )

        else:
            return

        productions_keys = self.productions
        production_keys_list = self.initial_symbol_as_first()
        non_terminals_count = len( production_keys_list )

        for maximum_index in range( 0, non_terminals_count ):
            indirect_recursions = list()
            indirect_replacements = list()

            outter_start_symbol = production_keys_list[maximum_index]
            outter_productions = productions_keys[outter_start_symbol]
            log( 32, "1. outter_start_symbol: %s", outter_start_symbol )
            log( 32, "1. outter_productions: %s", outter_productions )

            for index in range( 0, maximum_index ):
                inner_start_symbol = production_keys_list[index]
                inner_productions = productions_keys[inner_start_symbol]

                log( 32, "1.2 inner_start_symbol: %s", inner_start_symbol )
                log( 32, "1.2 inner_productions: %s", inner_productions )
                log( 32, "1.2 outter_productions: %s", outter_productions )

                for outter_production in outter_productions(1):
                    log( 32, "1.2.3 outter_production: %s", outter_production )
                    remove_outter_production = False
                    outter_production_first_symbol = outter_production[0]

                    if type( outter_production_first_symbol ) is NonTerminal:

                        if outter_production_first_symbol == inner_start_symbol:
                            indirect_recursions.append( outter_production )

                            for inner_production in inner_productions(1):
                                remove_outter_production = True
                                new_production = outter_production.replace( 0, inner_production )

                                self.add_production( outter_start_symbol, new_production )
                                indirect_replacements.append( inner_production )

                    if remove_outter_production:
                        self.remove_production( outter_start_symbol, outter_production, False )

            direct_recursions = set()
            direct_recursions_list = list()
            direct_replacements = list()
            new_outter_start_symbol = self.new_symbol( outter_start_symbol )

            for outter_production in outter_productions:

                if type( outter_production[0] ) is NonTerminal:

                    if outter_production[0] == outter_start_symbol:
                        direct_recursions.add( outter_production )
                        direct_recursions_list.append( outter_production )

            log( 32, "self: \n%s", self )
            log( 32, "2. new_outter_start_symbol: %s", new_outter_start_symbol )
            log( 32, "2. direct_recursions: %s", direct_recursions )
            self._save_history( "Eliminate indirect left recursion" )
            self._save_data( "Indirect recursion for elimination: %s -> %s", indirect_recursions, indirect_replacements )

            if direct_recursions:

                for outter_production in outter_productions(1):
                    log( 32, "2.1 outter_productions: %s", outter_productions )

                    if outter_production in direct_recursions:
                        new_production = outter_production.new()
                        new_production.remove_non_terminal( 0 )
                        new_production.add( new_outter_start_symbol[0].new() )
                        self.add_production( new_outter_start_symbol, new_production )

                    else:
                        new_production = outter_production.new()
                        new_production.add( new_outter_start_symbol[0].new() )
                        direct_replacements.append( new_production )
                        self.add_production( outter_start_symbol, new_production )

                    self.remove_production( outter_start_symbol, outter_production, False )

                self.add_production( new_outter_start_symbol, epsilon_production.new() )

            log( 32, "self: \n%s", self )
            self._save_history( "Eliminate direct left recursion" )
            self._save_data( "Direct recursion for elimination: %s -> %s", direct_recursions_list, direct_replacements )

        self._save_history( "Eliminating Left Recursion", IntermediateGrammar.END )

    def has_indirect_factors(self):
        """
            Checks whether there are indirect factors on this grammar.
        """
        production_keys = self.productions

        for start_symbol in production_keys:
            start_productions = production_keys[start_symbol]

            for start_production in start_productions:
                first_symbol = start_production[0]

                if type( first_symbol ) is NonTerminal:
                    return True

        return False

    def factors(self):
        """
            Call `eliminate_indirect_factors()` then returns a list with tuple on the format
            (NonTerminal, Terminal) representing this grammar nondeterministic factors for each non
            deterministic non terminal start symbol.

            If the list contains duplicated entries, it means this grammar is non factored, i.e.,
            non deterministic.
        """
        factors = []
        first_terminals = self.first_terminals()
        production_keys = self.productions

        for start_symbol in production_keys:
            productions = production_keys[start_symbol]

            for production in productions:
                first_from = self.first_from( production, first_terminals )
                # log( 1, "first_from: %-6s -> %s", production, first_from )

                for first_terminal in first_from:

                    if len( first_terminal ):
                        factors.append( ( start_symbol, Production( [first_terminal.new()], lock=True ) ) )

        return factors

    def has_duplicated_factors(self):
        """
            Call `factors()` and check whether there are duplicated entries in the factors list.

            How do I check if there are duplicates in a flat list?
            https://stackoverflow.com/questions/1541797/how-do-i-check-if-there-are-duplicates-in-a-flat-list
        """
        factors = self.factors()
        factors_length = len( factors )
        return factors_length and factors_length != len( set( factors ) )

    def is_factored(self):
        """
            Determines whether this grammar is factored, i.e., deterministic or nondeterministic.
        """
        return not self.has_left_recursion() and not self.has_duplicated_factors()

    def factor_it(self, maximum_steps=5):
        """
            Try to factor the this grammar in the `maximum_steps` given. Return True is the
            factorization was successful, False otherwise.
        """
        log( 16, "self: \n%s", self )
        self._save_history( "Factoring", IntermediateGrammar.BEGINNING )

        was_factored = False
        self.last_factoring_step = 0

        if self.has_left_recursion():
            self.eliminate_left_recursion()

        while True:
            self.last_factoring_step += 1
            is_factored = not self.has_duplicated_factors()

            if is_factored:
                was_factored = True
                break

            if self.last_factoring_step > maximum_steps:
                break

            self.eliminate_indirect_factors()
            self.eliminate_direct_factors()

        self._save_history( "Factoring", IntermediateGrammar.END )
        return was_factored

    def eliminate_indirect_factors(self):
        """
            Converts all indirect factors on this grammar to direct factors.
        """
        self._save_history( "Eliminating Indirect Factors", IntermediateGrammar.BEGINNING )
        old_counter = -1
        current_counter = 0

        production_keys = self.productions
        non_deterministic_factors_list = []

        while old_counter != current_counter:
            old_counter = current_counter

            for start_symbol in production_keys:
                start_productions = production_keys[start_symbol]

                for start_production in start_productions(1):
                    first_symbol = start_production[0]

                    if type( first_symbol ) is NonTerminal:
                        remove_production = False
                        first_symbol_productions = production_keys[first_symbol]
                        non_deterministic_factors_list.append( ( start_production, first_symbol ) )

                        for first_symbol_production in first_symbol_productions:
                            remove_production = True
                            new_production = start_production.replace( 0, first_symbol_production )
                            self.add_production( start_symbol, new_production )

                        if remove_production:
                            current_counter += 1
                            self.remove_production( start_symbol, start_production )

        self._save_history( "Eliminating Indirect Factors", IntermediateGrammar.END )
        self._save_data( "Indirect factors for elimination: %s", non_deterministic_factors_list )
        log( 16, "self out: \n%s", self )

    def eliminate_direct_factors(self):
        """
            Converts all direct factors on this grammar to deterministic factors.
        """
        self._save_history( "Eliminating Direct Factors", IntermediateGrammar.BEGINNING )
        production_keys = self.productions

        non_deterministic_factors_list = sorted( get_duplicated_elements( self.factors() ) )
        non_deterministic_factors_dictionary = {}

        for start_symbol in production_keys:
            non_deterministic_factors_dictionary[start_symbol]  = []

        self._save_data( "Direct factors for elimination: %s", non_deterministic_factors_list )
        for factor_symbol, factor_terminal in reversed( non_deterministic_factors_list ):
            non_deterministic_factors_dictionary[factor_symbol].append( factor_terminal )

        for start_symbol in production_keys:
            start_productions = self.productions[start_symbol]
            log( 16, "start_symbol: %s", start_symbol )
            log( 16, "start_productions: %s", start_productions )

            if start_symbol in non_deterministic_factors_dictionary:
                start_symbol_non_deterministic_factors_dictionary = non_deterministic_factors_dictionary[start_symbol]

                log( 16, "non_deterministic_factors: %s", start_symbol_non_deterministic_factors_dictionary )
                start_productions.not_iterate_over_new_items( len( start_symbol_non_deterministic_factors_dictionary ) )

                while True:

                    # Picks up a random nondeterministic symbol to factoring
                    if start_symbol_non_deterministic_factors_dictionary:
                        non_deterministic_factor = start_symbol_non_deterministic_factors_dictionary.pop()

                    else:
                        break

                    new_factor_start_symbol = self.new_symbol( start_symbol, True )
                    direct_factors_productions = {}
                    log( 16, "non_deterministic_factor: %s", non_deterministic_factor )
                    log( 16, "new_factor_start_symbol: %s", new_factor_start_symbol )

                    for start_production in start_productions:

                            if start_production[0] == non_deterministic_factor[0]:
                                direct_factors_productions[start_production] = non_deterministic_factor

                    direct_factors_productions = direct_factors_productions
                    log( 16, "direct_factors_productions: %s", direct_factors_productions )

                    if direct_factors_productions:
                        has_added_first_production = False

                        for start_production in start_productions(1):

                            if start_production in direct_factors_productions:

                                if not has_added_first_production:
                                    has_added_first_production = True
                                    new_start_production = direct_factors_productions[start_production].new()
                                    new_start_production.add( new_factor_start_symbol[0].new() )
                                    self.add_production( start_symbol, new_start_production )

                                new_factor_production = start_production.new()
                                new_factor_production.remove( 0 )

                                self.add_production( new_factor_start_symbol, new_factor_production )
                                self.remove_production( start_symbol, start_production )

        self._save_history( "Eliminating Direct Factors", IntermediateGrammar.END )
        log( 16, "self out: \n%s", self )

    def fertile(self):
        """
            Return a set with the fertile non terminal's start symbols.
        """
        # log( 1, "self: \n%s", self )
        fertile = set()
        production_keys = self.productions

        old_counter = -1
        current_counter = 0

        # Create the initial fertile Non Terminal's sets
        for start_symbol in production_keys:
            current_terminals = self.terminals_productions( start_symbol )
            # log( 1, "start_symbol: %s, current_terminals: %s", start_symbol, current_terminals )

            if current_terminals:
                fertile.add( start_symbol )

        while old_counter != current_counter:
            old_counter = current_counter

            for start_symbol in production_keys:
                start_productions = production_keys[start_symbol]

                for production in start_productions:
                    all_fertile = True

                    for symbol in production:

                        if type( symbol ) is Terminal:
                            continue

                        if type( symbol ) is NonTerminal:

                            if symbol in fertile:
                                continue

                            else:
                                all_fertile = False
                                break

                    if all_fertile and start_symbol not in fertile:
                        current_counter += 1
                        fertile.add( start_symbol )

        return fertile

    def eliminate_infertile(self):
        """
            Eliminates all non fertile non terminal's symbols with their productions.
        """
        self._save_history( "Eliminating Infertile Symbols", IntermediateGrammar.BEGINNING )
        fertile = self.fertile()
        infertile = list()
        production_keys = self.productions

        for start_symbol in production_keys(1):
            start_productions = production_keys[start_symbol]

            for production in start_productions(1):
                all_fertile = True

                for symbol in production:

                    if type( symbol ) is NonTerminal:

                        if symbol in fertile:
                            continue

                        else:
                            all_fertile = False
                            break

                if not all_fertile:
                    infertile.append( "%s -> %s" % ( start_symbol, production ) )
                    self.remove_production( start_symbol, production, False )

                    if not start_productions:
                        self.remove_start_non_terminal( start_symbol, False )

        self._save_history( "Eliminating Infertile Symbols", IntermediateGrammar.END )
        self._save_data( "Infertile symbols: %s", infertile )

    def reachable(self):
        """
            Return a set with the reachable terminal's and non terminal's symbols.
        """
        production_keys = self.productions
        reachable_terminals = set()
        reachable_non_terminals = DynamicIterationDict( [self.initial_symbol.non_terminals(0)] )

        for start_symbol in reachable_non_terminals:
            start_productions = production_keys[start_symbol]

            for production in start_productions:

                for symbol in production:

                    if type( symbol ) is Terminal:
                        reachable_terminals.add( symbol )

                    if type( symbol ) is NonTerminal:
                        reachable_non_terminals.add( symbol )

        return reachable_terminals | set( reachable_non_terminals )

    def eliminate_unreachable(self):
        """
            Eliminates all unreachable terminal's and non terminal symbols with their productions.
        """
        self._save_history( "Eliminating Unreachable Symbols", IntermediateGrammar.BEGINNING )
        reachable = self.reachable()
        production_keys = self.productions

        for start_symbol in production_keys(1):
            # log( 1, "1. start_symbol: %s, production_keys: %s", start_symbol, production_keys )

            if start_symbol not in reachable:
                self.remove_start_non_terminal( start_symbol )
                continue

            start_productions = production_keys[start_symbol]
            # log( 1, "2. start_productions: %s", start_productions )

            for production in start_productions:
                # log( 1, "2. production: %s", production )
                all_reachable = True

                for symbol in production:

                    if symbol in reachable:
                        continue

                    else:
                        all_reachable = False
                        break

                if not all_reachable:
                    self.remove_production( start_symbol, production )

        # log( 1, "productions: %s", self.productions )
        self._save_history( "Eliminating Unreachable Symbols", IntermediateGrammar.END )

    def eliminate_unuseful(self):
        """
            Eliminates all infertile and unreachable terminal's and non terminal's symbols.
        """
        self._save_history( "Eliminating Unuseful Symbols", IntermediateGrammar.BEGINNING )
        self.eliminate_infertile()
        self.eliminate_unreachable()
        self._save_history( "Eliminating Unuseful Symbols", IntermediateGrammar.END )

    def simple_non_terminals(self):
        """
            For each non terminal start symbol, calculates the reachable terminal only by simple
            productions.

            Return a dictionary with the non terminal's reachable by simple productions for each non
            terminal start symbol
        """
        self.convert_to_epsilon_free()
        old_counter = -1
        current_counter = 0

        production_keys = self.productions
        simple_non_terminals = {}

        # Create the initial simple_non_terminals's sets within their own as elements
        for symbol in production_keys:
            simple_non_terminals[symbol] = DynamicIterationDict([symbol])

        while old_counter != current_counter:
            old_counter = current_counter

            for start_symbol in production_keys:
                start_productions = production_keys[start_symbol]

                for production in start_productions:

                    if len( production ) == 1:
                        non_terminal = production.non_terminals( 0 )

                        if non_terminal:

                            if Production.copy_productions_except_epsilon(
                                    simple_non_terminals[non_terminal], simple_non_terminals[start_symbol] ):
                                current_counter += 1

        return simple_non_terminals

    def has_simple_cycle(self):
        """
            Determines whether this grammar has direct cycle of simple non terminals `A +=> A` on
            any of its start non terminal's symbols.
        """
        production_keys = self.productions

        for non_terminal_to_check in production_keys:
            recursive_terminals = DynamicIterationDict([non_terminal_to_check])

            for non_terminal in recursive_terminals:
                productions = production_keys[non_terminal]

                for production in productions:
                    # log( 1, "production: %s", production )

                    for symbol in production:
                        # log( 1, "symbol: %s", symbol )

                        if type( symbol ) is NonTerminal and len( production ) == 1:

                            if symbol == non_terminal_to_check:
                                # log( 1, "recursive_terminals: %s", recursive_terminals )
                                return True

                            if symbol not in recursive_terminals:
                                recursive_terminals.add( symbol )

            # log( 1, "recursive_terminals: %s", recursive_terminals )
            return False

    def eliminate_simple_non_terminals(self):
        """
            Eliminates all unreachable terminal's and non terminal symbols with their productions.
        """
        self._save_history( "Eliminating Simple Productions", IntermediateGrammar.BEGINNING )
        simple_non_terminals = self.simple_non_terminals()
        production_keys = self.productions

        for start_symbol in production_keys:

            for production in simple_non_terminals[start_symbol]:
                self.copy_productions_for_one_non_terminal( production, start_symbol )

        for start_symbol in production_keys:
            start_productions = production_keys[start_symbol]

            for production in start_productions:

                if production in simple_non_terminals:
                    self.remove_production( start_symbol, production )

        self._save_history( "Eliminating Simple Productions", IntermediateGrammar.END )
        self._save_data( "Simple Non Terminals: %s", "; ".join( "%s -> %s" % ( key, element.keys() )
               for key, element in simple_non_terminals.items() ) )

    def convert_to_proper(self):
        """
            1. Call `convert_to_epsilon_free()` because it can create cycles
            2. Call `eliminate_simple_non_terminals()` because it can create unuseful (infertile and unreachable) symbols.
            3. Call `eliminate_unuseful()` to finally clear the grammar.
        """
        self._save_history( "Converting to Proper", IntermediateGrammar.BEGINNING )

        if not self.is_epsilon_free():
            self.convert_to_epsilon_free()

        if self.has_simple_cycle():
            self.eliminate_simple_non_terminals()

        self.eliminate_unuseful()
        self._save_history( "Converting to Proper", IntermediateGrammar.END )

    def is_empty(self):
        """
            Return `True` if this grammar language is empty, i.e., generates no sentences.

            Removes all unuseful symbols, and if the initial symbol was removed, then a new initial
            symbol only with the production `S -> S` will be added to this grammar.
        """
        self.eliminate_unuseful()
        return self._is_empty()

    def _is_empty(self):
        """
            Return `True` if this grammar language is empty, i.e., generates no sentences.
        """
        initial_symbol = self.initial_symbol
        return self.has_production( initial_symbol, initial_symbol ) and len( self.productions[initial_symbol] ) == 1

    def is_finite(self):
        """
            Return `True` if this grammar language is finite, i.e., generates a finite set of sentences.

            Call `is_empty()` and `is_infinite()` and if both are `False`, then this language is finite.
        """
        return not self.is_empty() and not self.is_infinite()

    def is_infinite(self):
        """
            Return `True` if this grammar language is infinite, i.e., generates a infinite set of sentences.

            Checks whether there is fertile derivation cycle. If so, then this grammar generates a
            infinite language.
        """

        if not self.is_empty():
            self.eliminate_simple_non_terminals()
            self.eliminate_unuseful()

            for start_symbol in self.productions:

                if self.has_recursion_on_the_non_terminal( start_symbol ):
                    return True

        return False

    def first_non_terminals(self):
        """
            Calculates the start production symbols non terminal's FIRST set.
        """
        first = {}
        production_keys = self.productions

        old_counter = -1
        current_counter = 0

        # Create the initial FIRST Non Terminal's sets
        for symbol in production_keys:
            first[symbol] = set()

        while old_counter != current_counter:
            old_counter = current_counter

            for start_symbol in production_keys:
                start_productions = production_keys[start_symbol]

                for production in start_productions:

                    # If there is a production X → Y1Y2..Yk then add first(Y1Y2..Yk) to first(X)
                    for symbol in production:

                        if type( symbol ) is NonTerminal:

                            if symbol not in first[start_symbol]:
                                first[start_symbol].add( symbol )
                                current_counter += 1

                            if Production.copy_productions_except_epsilon( first[symbol], first[start_symbol] ):
                                current_counter += 1

                            # log( 1, "symbol: %s, production: %-6s, first: %s", symbol, production, first[symbol] )
                            if self.has_production( symbol, epsilon_production ):
                                continue

                            else:
                                break

                        else:
                            break

        return first

    def first_terminals(self):
        """
            Calculate this grammar terminal's FIRST's set for each non terminal.

            First and Follow Sets
            https://www.jambe.co.nz/UNI/FirstAndFollowSets.html

            @return a dictionary with the first for each non terminal start symbol
        """
        first_terminals = {}
        production_keys = self.productions

        old_counter = -1
        current_counter = 0

        # Create the initial FIRST's sets
        for symbol in production_keys:
            first_terminals[symbol] = set()

        while old_counter != current_counter:
            old_counter = current_counter

            for start_symbol in production_keys:
                start_productions = production_keys[start_symbol]

                for production in start_productions:

                    # If there is a production X → Y1Y2..Yk then add first(Y1Y2..Yk) to first(X)
                    for symbol in production:

                        # If X is a terminal then First(X) is just X!
                        # If there is a production X → ε then add ε to first(X)
                        if type( symbol ) is Terminal:
                            # symbol = Terminal( symbol.str[0], lock=True )

                            if symbol not in first_terminals[start_symbol]:
                                first_terminals[start_symbol].add( symbol )
                                current_counter += 1
                            break

                        if type( symbol ) is NonTerminal:

                            if Production.copy_productions_except_epsilon( first_terminals[symbol], first_terminals[start_symbol] ):
                                current_counter += 1

                            # log( 1, "symbol: %s, production: %-6s, first: %s", symbol, production, first_terminals[symbol] )
                            if epsilon_terminal in first_terminals[symbol]:

                                # If First(Y1) First(Y2)..First(Yk) all contain ε, then add ε to First(Y1Y2..Yk) as well
                                if production.is_last( symbol ):

                                    if epsilon_terminal not in first_terminals[start_symbol]:
                                        first_terminals[start_symbol].add( epsilon_terminal )
                                        current_counter += 1

                            else:
                                break

        return first_terminals

    def first_from(self, symbols, first_terminals=None):
        """
            Given a list of `symbols` get their FIRST symbols set.
        """
        following_first = set()

        if not first_terminals:
            first_terminals = self.first_terminals()

        for symbol in symbols:
            symbol_type = type( symbol )

            if symbol_type is NonTerminal:
                first_set = first_terminals[symbol]
                following_first.update( first_set )

                if epsilon_terminal not in first_set:
                    break

            elif symbol_type is Terminal:
                following_first.add( symbol )
                break

            else:
                raise RuntimeError( "Expecting a Terminal or NonTerminal symbol. Got: %s! (%s) \n%s" % ( type( symbol ), symbol, self ) )

        return following_first

    def follow_terminals(self, first_terminals=None):
        """
            Calculate this grammar FOLLOW's set for each non terminal.

            @return a dictionary with the follow for each non terminal start symbol
        """
        follow_terminals = {}
        production_keys = self.productions

        old_counter = -1
        current_counter = 0

        if not first_terminals:
            first_terminals = self.first_terminals()

        # Create the initial FOLLOW's sets
        for symbol in production_keys:
            follow_terminals[symbol] = set()

        # First put $ (the end of input marker) in Follow(S) (S is the start symbol)
        follow_terminals[self.initial_symbol].add( end_of_string_terminal )

        while old_counter != current_counter:
            old_counter = current_counter

            for start_symbol in production_keys:
                start_productions = production_keys[start_symbol]

                for production in start_productions:

                    # If there is a production A → aBb, (where a can be a whole string) then
                    # everything in FIRST(b) except for ε is placed in FOLLOW(B).
                    for current_symbol in production:

                        if type( current_symbol ) is NonTerminal:
                            next_symbol = production.peek_next()

                            if next_symbol:
                                following_first = self.first_from( production.following_symbols(), first_terminals )

                                if Production.copy_productions_except_epsilon( following_first, follow_terminals[current_symbol] ):
                                    # log( 1, "1. start_symbol: %s, current_symbol: %s, next_symbol: %-4s, Adding: %s", start_symbol, current_symbol, next_symbol, following_first )
                                    current_counter += 1

                                if epsilon_terminal in following_first:

                                    if Production.copy_productions_except_epsilon( follow_terminals[start_symbol], follow_terminals[current_symbol] ):
                                        # log( 1, "2. start_symbol: %s, current_symbol: %s, next_symbol: %-4s, Adding: %s", start_symbol, current_symbol, next_symbol, follow_terminals[start_symbol] )
                                        current_counter += 1

                            else:

                                if Production.copy_productions_except_epsilon( follow_terminals[start_symbol], follow_terminals[current_symbol] ):
                                    # log( 1, "3. start_symbol: %s, current_symbol: %s, next_symbol: %-4s, Adding: %s", start_symbol, current_symbol, next_symbol, follow_terminals[start_symbol] )
                                    current_counter += 1

        return follow_terminals

