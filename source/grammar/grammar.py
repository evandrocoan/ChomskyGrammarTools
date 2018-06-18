#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from threading import Lock
from debug_tools import getLogger

import lark
from typing import Dict, Set

from .symbols import Terminal
from .symbols import NonTerminal

from .production import Production
from .production import epsilon_production
from .production import end_of_string_terminal

from .utilities import getCleanSpaces
from .utilities import DynamicIterationSet
from .utilities import sort_alphabetically_and_by_length

from .tree_transformer import ChomskyGrammarTreeTransformer

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, __name__ )
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
        terminal        : ( DIGIT | LCASE_LETTER | dash_phi_hyphen | star | plus | open_paren | close_paren )+
        non_terminal    : UCASE_LETTER+ ( UCASE_LETTER | DIGIT | quote )*
        new_line        : NEWLINE
        quote           : "'"
        dash_phi_hyphen : "-"
        space           : " "
        star            : "*"
        plus            : "+"
        open_paren      : "("
        close_paren     : ")"

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

        def create_grammar_line(non_terminal_start, productions):
            productions_string = []

            for production in productions:
                productions_string.append( str( production ) )

            log( 4, "productions:        %s", productions )
            log( 4, "productions_string: %s", productions_string )

            return "{:>{biggest}} -> {}".format( str( non_terminal_start ),
                    " | ".join( sort_alphabetically_and_by_length( productions_string ) ), biggest=biggest )

        if self.initial_symbol in self.productions:
            grammar_lines.append( create_grammar_line( self.initial_symbol, self.productions[self.initial_symbol] ) )

        else:
            raise RuntimeError( "Your grammar has an invalid initial_symbol! %s, %s" % ( self.initial_symbol, self.productions ) )

        for non_terminal in sorted( set( self.productions.keys() ) - {self.initial_symbol} ):
            grammar_lines.append( create_grammar_line( non_terminal, self.productions[non_terminal] ) )

        return "\n".join( grammar_lines )

    def _get_table_biggest_elements(self):
        biggest_label_length = 0

        for production in self.productions.keys():
            production_length = len( str( production ) )

            if production_length > biggest_label_length:
                biggest_label_length = production_length

        log( 4, "biggest_label_length: %s", biggest_label_length )
        return biggest_label_length

    def __init__(self):
        """
            Create a new grammar.
        """
        ## A dictionary with productions this grammar can generates
        self.productions = {}
        self._initial_symbol = ""

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

        if isinstance( value, Production ) and len( value ) == 1:
            value.lock()
            self._initial_symbol = value

        else:
            raise ValueError( "Error: The initial must be an Production with length 1! %s" % repr( value ) )

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
        AST = cls.parse( "\n".join( getCleanSpaces( input_text_form, keepSpaceSepators=True ) ) )
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

        if type( start_symbol ) is not Production:
            raise RuntimeError( "Your start_symbol is not an instance of Production! %s, %s" % ( start_symbol, production ) )

        if type( production ) is not Production:
            raise RuntimeError( "Your production is not an instance of Production! %s, %s" % ( start_symbol, production ) )

        if not len( start_symbol ):
            raise RuntimeError( "Grammar start non terminal cannot be Epsilon! %s -> %s", start_symbol, production )

        production.lock()
        start_symbol.lock()

        if start_symbol not in self.productions:
            self.productions[start_symbol] = set()

        self.productions[start_symbol].add( production )

    def has_production(self, start_symbol, production):
        """
            Returns True if the `start_symbol` has the given `production`.
        """
        return production in self.productions[start_symbol]

    def terminals_productions(self, non_terminal_start):
        """
            Given the non terminal `non_terminal_start`, return all reachable productions only composed
            with terminal's.
        """
        productions = self.productions[non_terminal_start]
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

    def get_non_terminals(self, start_symbol):
        """
            Given a `start_symbol` as S, return all its non terminal's reachable from it, with or
            without terminal's together.
        """
        return self.get_symbols_composition( self.productions[start_symbol], NonTerminal )

    def get_terminals(self, symbol):
        """
            Given a `start_symbol` as S, return all its terminal's reachable from it, with or
            without non terminal's together.
        """
        return self.get_symbols_composition( self.productions[symbol], Terminal )

    @staticmethod
    def get_symbols_composition(productions, symbolType):
        """
            For each production in `productions`, get all symbol of type `symbolType` they are composed.
        """
        symbols_composition = set()

        for symbol in productions:
            symbols = symbol._get_symbols( symbolType )
            symbols_composition.update( symbols )

        return symbols_composition

    def assure_existing_symbols(self):
        """
            Checks whether the grammar uses non existent non terminal symbols as `S -> Aa | a` or if
            there is a empty start symbol `S ->`.
        """
        production_keys = self.productions.keys()
        start_non_terminals = self.get_symbols_composition( production_keys, NonTerminal )

        for non_terminal_start in production_keys:
            non_terminals = self.get_non_terminals( non_terminal_start )

            for non_terminal in non_terminals:

                if non_terminal not in start_non_terminals:
                    raise RuntimeError( "Invalid Non Terminal `%s` added to the grammar: \n%s" % ( non_terminal, self ) )

        if self.initial_symbol not in self.productions:
            raise ValueError( "Error: The new initial symbol has not productions! %s" % repr( self.initial_symbol ) )

    def is_epsilon_free(self):
        """
            Return `True` if the start symbol is recursive and has epsilon transitions or if other
            non initial symbol start non terminal have epsilon.
        """

        for non_terminal in self.productions.keys():

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
        recursive_terminals = DynamicIterationSet([non_terminal_to_check])

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

    def get_non_terminal_epsilon(self):
        """
            Creates the non terminal's epsilon set, within all non terminal's which lead to epsilon
            with 0 or more transitions.
        """
        old_counter = -1
        current_counter = 0

        production_keys = self.productions.keys()
        non_terminal_epsilon = DynamicIterationSet()

        for non_terminal_start in production_keys:

            if self.has_production( non_terminal_start, epsilon_production ):
                non_terminal_epsilon.add( non_terminal_start )

        while current_counter != old_counter:
            old_counter = current_counter

            for non_terminal_start in production_keys:
                productions = self.productions[non_terminal_start]

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

                    if all_symbols_go_to_epsilon and non_terminal_start not in non_terminal_epsilon:
                        non_terminal_epsilon.add( non_terminal_start )
                        current_counter += 1

        # log( 1, "non_terminal_epsilon: %s", non_terminal_epsilon )
        return non_terminal_epsilon

    def convert_to_epsilon_free(self):
        """
            Convert the current grammar to a epsilon free grammar.
        """
        # log( 1, "self: \n%s", self )
        non_terminal_epsilon = self.get_non_terminal_epsilon()

        for non_terminal_start in set( self.productions.keys() ):
            non_terminal_productions = set( self.productions[non_terminal_start] )

            for production in non_terminal_productions:

                for combination in production.combinations( non_terminal_epsilon ):
                    # log( 1, "combination: %s", combination )
                    self.add_production( non_terminal_start, combination )

            self.remove_production_from_non_terminal( non_terminal_start, epsilon_production )

        if self.initial_symbol in non_terminal_epsilon:

            if self.has_recursion_on_the_non_terminal( self.initial_symbol ):
                new_initial_symbol = self.get_new_initial_symbol()
                self.copy_productions_for_one_non_terminal( self.initial_symbol, new_initial_symbol )
                self.initial_symbol = new_initial_symbol

            self.add_production( self.initial_symbol, epsilon_production )

    def remove_production_from_non_terminal(self, start_symbol, production):
        """
            Given a `start_symbol` remove its `production`.

            If was the last production, then the `start_symbol` symbol is also removed from the
            grammar `productions` and everywhere it is mentioned.
        """
        self.productions[start_symbol].discard( production )

        if not self.productions[start_symbol]:
            self.remove_start_non_terminal( start_symbol )

    def remove_start_non_terminal(self, start_non_terminal):
        """
            Given a `start_non_terminal` remove it from the grammar and all productions which to it.

            If it was a initial symbol, `clean_initial_symbol()` will also be called.
        """
        production_keys = set( self.productions.keys() )

        for start_symbol in production_keys:
            start_productions = set( self.productions[start_symbol] )

            for production in start_productions:

                for symbol in production:

                    if symbol == start_non_terminal:
                        self.remove_production_from_non_terminal( start_symbol, production )
                        break

        del self.productions[start_non_terminal]
        self.clean_initial_symbol( start_non_terminal )

    def clean_initial_symbol(self, start_symbol):
        """
            Replace the current initial symbol creating a new empty initial symbol such `S -> S` by
            querying `get_new_initial_symbol()` for a new initial symbol.
        """

        if self.initial_symbol == start_symbol:
            # log( 1, "WARNING: Removing the gramar initial symbol!" )
            new_initial_symbol = self.get_new_initial_symbol()

            self.add_production( new_initial_symbol, new_initial_symbol )
            self.initial_symbol = new_initial_symbol

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

        for production in secondGrammarProductions:
            self.add_production( non_terminal_destine, production )

    def get_new_initial_symbol(self, secondGrammar=None):
        """
            Search for a new initial symbol name until find one in the form S'''... and returns it.

            If given a `secondGrammar`, also try to find a new initial symbol which is unique for
            both grammars.
        """
        current_symbols = set()
        new_initial_symbol = 'S'

        for non_terminal in self.productions.keys():
            current_symbols.add( non_terminal )

        if secondGrammar:

            for non_terminal in secondGrammar.productions.keys():
                current_symbols.add( non_terminal )

        while True:
            new_initial_symbol += "'"

            if new_initial_symbol not in current_symbols:
                return Production( symbols=[NonTerminal( new_initial_symbol )], lock=True )


    def left_recursion(self):
        """
            Determines whether this grammar has left recursion on any of its start non terminal's
            symbols.
        """
        left_recursion = {}
        return left_recursion

    def has_left_recursion(self):
        """
            Determines whether this grammar has left recursion on any of its start non terminal's
            symbols.
        """
        return bool( not self.left_recursion() )

    def factors(self):
        """
            Returns a dictionary with this grammar nondeterministic factors set for each non
            deterministic non terminal start symbol.
        """
        factors = {}
        return factors

    def is_factored(self):
        """
            Determines whether this grammar is factored, i.e., deterministic or nondeterministic.
        """
        return bool( not self.factors() )

    def fertile(self):
        """
            Return a set with the fertile non terminal's start symbols.
        """
        # log( 1, "self: \n%s", self )
        fertile = set()
        production_keys = self.productions.keys()

        old_counter = -1
        current_counter = 0

        # Create the initial fertile Non Terminal's sets
        for non_terminal_start in production_keys:
            current_terminals = self.terminals_productions( non_terminal_start )
            # log( 1, "non_terminal_start: %s, current_terminals: %s", non_terminal_start, current_terminals )

            if current_terminals:
                fertile.add( non_terminal_start )

        while old_counter != current_counter:
            old_counter = current_counter

            for start_symbol in production_keys:
                start_productions = self.productions[start_symbol]

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
        fertile = self.fertile()
        production_keys = set( self.productions.keys() )

        for start_symbol in production_keys:
            # log( 1, "start_symbol: %s (%d)", start_symbol, start_symbol in self.productions )

            # While iterating over this set, production keys may be removed indirectly
            if start_symbol not in self.productions:
                continue

            start_productions = set( self.productions[start_symbol] )

            for production in start_productions:
                all_fertile = True

                for symbol in production:

                    if type( symbol ) is NonTerminal:

                        if symbol in fertile:
                            continue

                        else:
                            all_fertile = False
                            break

                if not all_fertile:
                    self.remove_production_from_non_terminal( start_symbol, production )

    def reachable(self):
        """
            Return a set with the reachable terminal's and non terminal's symbols.
        """
        reachable_terminals = set()
        reachable_non_terminals = DynamicIterationSet( [self.initial_symbol.get_non_terminals(0)] )

        for start_symbol in reachable_non_terminals:
            start_productions = self.productions[start_symbol]

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
        reachable = self.reachable()
        production_keys = set( self.productions.keys() )

        for start_symbol in production_keys:

            if start_symbol not in reachable:
                self.remove_start_non_terminal( start_symbol )
                continue

            start_productions = set( self.productions[start_symbol] )

            for production in start_productions:
                all_reachable = True

                for symbol in production:

                    if symbol in reachable:
                        continue

                    else:
                        all_reachable = False
                        break

                if not all_reachable:
                    self.remove_production_from_non_terminal( start_symbol, production )

    def eliminate_unuseful(self):
        """
            Eliminates all infertile and unreachable terminal's and non terminal's symbols.
        """
        self.eliminate_infertile()
        self.eliminate_unreachable()

    def get_simple_non_terminals(self):
        """
            For each non terminal start symbol, calculates the reachable terminal only by simple
            productions.

            @return a dictionary with the non terminal's reachable by simple productions for each
                non terminal start symbol
        """
        self.convert_to_epsilon_free()
        simple_non_terminals = {}
        production_keys = self.productions.keys()

        old_counter = -1
        current_counter = 0

        # Create the initial simple_non_terminals's sets within their own as elements
        for symbol in production_keys:
            simple_non_terminals[symbol] = set([symbol])

        while old_counter != current_counter:
            old_counter = current_counter

            for start_symbol in production_keys:
                start_productions = self.productions[start_symbol]

                for production in start_productions:

                    if len( production ) == 1:
                        non_terminal = production.get_non_terminals( 0 )

                        if non_terminal:

                            if Production.copy_productions_except_epsilon(
                                    simple_non_terminals[non_terminal], simple_non_terminals[start_symbol] ):
                                current_counter += 1

        return simple_non_terminals

    def eliminate_simple_non_terminals(self):
        """
            Eliminates all unreachable terminal's and non terminal symbols with their productions.
        """
        simple_non_terminals = self.get_simple_non_terminals()
        production_keys = set( self.productions.keys() )

        for start_symbol in production_keys:

            for production in simple_non_terminals[start_symbol]:
                self.copy_productions_for_one_non_terminal( production, start_symbol )

        for start_symbol in production_keys:

            # While iterating over this set, production keys may be removed indirectly
            if start_symbol not in self.productions:
                continue

            start_productions = set( self.productions[start_symbol] )

            for production in start_productions:

                if production in simple_non_terminals:
                    self.remove_production_from_non_terminal( start_symbol, production )

    def convert_to_proper(self):
        """
            1. Call `convert_to_epsilon_free()` because it can create cycles
            2. Call `eliminate_simple_non_terminals()` because it can create unuseful (infertile and unreachable) symbols.
            3. Call `eliminate_unuseful()` to finally clear the grammar.
        """
        self.convert_to_epsilon_free()
        self.eliminate_simple_non_terminals()
        self.eliminate_unuseful()

    def is_empty(self):
        """
            Return `True` if this grammar language is empty, i.e., generates no sentences.

            Removes all unuseful symbols, and if the initial symbol was removed, then a new initial
            symbol only with the production `S -> S` will be added to this grammar.
        """
        self.eliminate_unuseful()
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
        self.eliminate_simple_non_terminals()
        self.eliminate_unuseful()

        for start_symbol in self.productions.keys():

            if self.has_recursion_on_the_non_terminal( start_symbol ):
                return True

        return False

    def first_non_terminal(self):
        """
            Calculates the start production symbols non terminal's FIRST set.
        """
        first = {}
        production_keys = self.productions.keys()

        old_counter = -1
        current_counter = 0

        # Create the initial FIRST Non Terminal's sets
        for symbol in production_keys:
            first[symbol] = set()

        while old_counter != current_counter:
            old_counter = current_counter

            for start_symbol in production_keys:
                start_productions = self.productions[start_symbol]

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

    def first(self):
        """
            Calculate this grammar terminal's FIRST's set for each non terminal.

            First and Follow Sets
            https://www.jambe.co.nz/UNI/FirstAndFollowSets.html

            @return a dictionary with the first for each non terminal start symbol
        """
        first = {}
        production_keys = self.productions.keys()

        old_counter = -1
        current_counter = 0

        # Create the initial FIRST's sets
        for symbol in production_keys:
            first[symbol] = set()

        while old_counter != current_counter:
            old_counter = current_counter

            for start_symbol in production_keys:
                start_productions = self.productions[start_symbol]

                for production in start_productions:

                    # If there is a production X → Y1Y2..Yk then add first(Y1Y2..Yk) to first(X)
                    for symbol in production:

                        # If X is a terminal then First(X) is just X!
                        # If there is a production X → ε then add ε to first(X)
                        if type( symbol ) is Terminal:

                            if symbol not in first[start_symbol]:
                                first[start_symbol].add( symbol )
                                current_counter += 1
                            break

                        if type( symbol ) is NonTerminal:

                            if Production.copy_productions_except_epsilon( first[symbol], first[start_symbol] ):
                                current_counter += 1

                            # log( 1, "symbol: %s, production: %-6s, first: %s", symbol, production, first[symbol] )
                            if epsilon_production in first[symbol]:

                                # If First(Y1) First(Y2)..First(Yk) all contain ε, then add ε to First(Y1Y2..Yk) as well
                                if production.is_last( symbol ):

                                    if epsilon_production not in first[start_symbol]:
                                        first[start_symbol].add( epsilon_production )
                                        current_counter += 1

                            else:
                                break

        return first

    def get_first_from(self, symbols, first=None ):
        """
            Given a list of `symbols` get their FIRST symbols set.
        """
        following_first = set()

        if not first:
            first = self.first()

        for symbol in symbols:

            if type( symbol ) is Terminal:
                following_first.add( symbol )
                break

            if type( symbol ) is NonTerminal:
                following_first.update( first[symbol] )
                break

        return following_first

    def follow(self, first=None):
        """
            Calculate this grammar FOLLOW's set for each non terminal.

            @return a dictionary with the first for each non terminal start symbol
        """
        follow = {}
        production_keys = self.productions.keys()

        old_counter = -1
        current_counter = 0

        if not first:
            first = self.first()

        # Create the initial FOLLOW's sets
        for symbol in production_keys:
            follow[symbol] = set()

        # First put $ (the end of input marker) in Follow(S) (S is the start symbol)
        follow[self.initial_symbol].add( end_of_string_terminal )

        while old_counter != current_counter:
            old_counter = current_counter

            for start_symbol in production_keys:
                start_productions = self.productions[start_symbol]

                for production in start_productions:

                    # If there is a production A → aBb, (where a can be a whole string) then
                    # everything in FIRST(b) except for ε is placed in FOLLOW(B).
                    for current_symbol in production:

                        if type( current_symbol ) is NonTerminal:
                            next_symbol = production.peek_next()

                            if next_symbol:
                                following_first = self.get_first_from( production.following_symbols(), first )

                                if Production.copy_productions_except_epsilon( following_first, follow[current_symbol] ):
                                    # log( 1, "1. start_symbol: %s, current_symbol: %s, next_symbol: %-4s, Adding: %s", start_symbol, current_symbol, next_symbol, following_first )
                                    current_counter += 1

                                if epsilon_production in following_first:

                                    if Production.copy_productions_except_epsilon( follow[start_symbol], follow[current_symbol] ):
                                        # log( 1, "2. start_symbol: %s, current_symbol: %s, next_symbol: %-4s, Adding: %s", start_symbol, current_symbol, next_symbol, follow[start_symbol] )
                                        current_counter += 1

                            else:

                                if Production.copy_productions_except_epsilon( follow[start_symbol], follow[current_symbol] ):
                                    # log( 1, "3. start_symbol: %s, current_symbol: %s, next_symbol: %-4s, Adding: %s", start_symbol, current_symbol, next_symbol, follow[start_symbol] )
                                    current_counter += 1

        return follow

