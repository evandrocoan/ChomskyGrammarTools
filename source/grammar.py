#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from threading import Lock
from debug_tools import getLogger

import lark
from typing import Dict, Set

from .utilities import getCleanSpaces
from .utilities import epsilon_production

from .utilities import Production
from .utilities import Terminal
from .utilities import NonTerminal
from .utilities import DynamicIterationSet
from .utilities import ChomskyGrammarTreeTransformer

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, os.path.basename( os.path.dirname( os.path.abspath ( __file__ ) ) ) )
log( 1, "Importing " + __name__ )


class ChomskyGrammar():
    """
        Regular grammar object. Example grammar:
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
        terminal        : ( SIGNED_NUMBER | LCASE_LETTER | dash_phi_hyphen | star | plus | open_paren | close_paren )+
        non_terminal    : UCASE_LETTER+ ( UCASE_LETTER | DIGIT | quote )*
        new_line        : NEWLINE
        quote           : "'"
        dash_phi_hyphen : "-"
        space           : " "
        star            : "*"
        plus            : "+"
        close_paren     : "("
        open_paren      : ")"

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
            return "{:>{biggest}} -> {}".format( str( non_terminal_start ), " | ".join( sorted( productions_string ) ), biggest=biggest )

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

    def __init__(self, initial_symbol="", productions=None):
        # {'1': {( 'a', '' ), ( 'a', 'A' )}}
        self.productions = productions if productions else {}
        self.initial_symbol = initial_symbol

    def __len__(self):
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
                                grammar.initial_symbol = current_level

                    if level_name == 'non_terminals':
                        grammar.add( current_level, node )

        new_tree = ChomskyGrammarTreeTransformer().transform( AST )
        parse_tree( new_tree, 0, len( new_tree.children ) )

        log( 4, "\n%s", new_tree.pretty() )
        log( 4, "Result initial_symbol: %s", grammar.initial_symbol )
        log( 4, "Result productions:    %s", grammar.productions )
        log( 4, "Result grammar:        %s", grammar )
        grammar.assure_existing_symbols()
        return grammar

    def add(self, start_symbol, production):

        if type( start_symbol ) is not Production:
            raise RuntimeError( "Your start_symbol is not an instance of Production! %s, %s" % ( start_symbol, production ) )

        if type( production ) is not Production:
            raise RuntimeError( "Your production is not an instance of Production! %s, %s" % ( start_symbol, production ) )

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

    def get_non_terminals(self, symbol):
        """
            Given a start symbol as S, return all its non_terminal's reachable from it.
        """
        return self.get_non_terminals_composition( self.productions[symbol] )

    @staticmethod
    def get_non_terminals_composition(productions):
        """
            For each production in `productions`, get all NonTerminal's they are composed.
        """
        symbol_non_terminals = set()

        for symbol in productions:
            non_terminals = symbol.get_non_terminals()
            symbol_non_terminals.update( non_terminals )

        return symbol_non_terminals

    def assure_existing_symbols(self):
        """
            Checks whether the grammar uses non existent non terminal symbols as `S -> Aa | a`.
        """
        production_keys = self.productions.keys()
        start_non_terminals = self.get_non_terminals_composition( production_keys )

        for non_terminal_start in production_keys:
            non_terminals = self.get_non_terminals( non_terminal_start )

            for non_terminal in non_terminals:

                if non_terminal not in start_non_terminals:
                    raise RuntimeError( "Invalid Non Terminal `%s` added to the grammar: \n%s" % ( non_terminal, self ) )

    def first(self):
        """
            Calculate this grammar first set for each non terminal.

            @return a dictionary with the first for each non terminal start symbol
        """
        visited_symbols = set()
        production_keys = self.productions.keys()

        first = {}
        current_count = 0
        processed_symbols = -1

        # Create the initial FIRST's sets
        for symbol in sorted( production_keys ):
            first[symbol] = set()

        while processed_symbols != current_count:
            processed_symbols = current_count

            for start_symbol in production_keys:
                start_productions = self.productions[start_symbol]

                for production in start_productions:

                    # If there is a Production X → Y1Y2..Yk then add first(Y1Y2..Yk) to first(X)
                    for symbol in production:

                        # If X is a terminal then First(X) is just X!
                        # If there is a Production X → ε then add ε to first(X)
                        if type( symbol ) is Terminal:

                            if symbol not in first[start_symbol]:
                                first[start_symbol].add( symbol )
                                current_count += 1
                            break

                        if type( symbol ) is NonTerminal:

                            if Production.copy_productions_except_epsilon( first[symbol], first[start_symbol] ):
                                current_count += 1

                            if epsilon_production in first[symbol]:
                                # log( 1, "symbol: %s, production: %-6s, first: %s", symbol, production, first[symbol] )

                                # If First(Y1) First(Y2)..First(Yk) all contain ε, then add ε to First(Y1Y2..Yk) as well
                                if Production.is_last_production( symbol, production ):

                                    if epsilon_production not in first[start_symbol]:
                                        first[start_symbol].add( epsilon_production )
                                        current_count += 1

                            else:
                                break

        return first

