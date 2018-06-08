#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from threading import Lock
from debug_tools import getLogger

import lark
from typing import Dict, Set

from .utilities import getCleanSpaces

from .utilities import DynamicIterationSet

# level 2 -
log = getLogger( 127, os.path.basename( os.path.dirname( os.path.abspath ( __file__ ) ) ) )
log( 1, "Importing " + __name__ )


class RegularGrammar():
    """
        Regular grammar object. Example grammar:
        S -> aA | bB | a | b | &
        A -> aA | a
        B -> bB | b
    """

    _parser = lark.Lark( r"""
        productions   : empty_line* ( non_terminal_start "->" non_terminals end_symbol )* non_terminal_start "->" non_terminals end_symbol?
        non_terminals : production ( "|" production )*
        production    : epsilon | terminal non_terminal?

        // Forces them to appear in the tree as branches
        epsilon         : [] | "&"
        end_symbol      : ";" NEWLINE+ | NEWLINE+
        terminal        : SIGNED_NUMBER | LCASE_LETTER
        non_terminal    : ( dash_phi_hyphen | UCASE_LETTER )+ ( ( dash_phi_hyphen | UCASE_LETTER ) | DIGIT | quote )*
        empty_line      : NEWLINE
        quote           : "'"
        dash_phi_hyphen : "-"

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
        %ignore WS_INLINE
    """, start='productions' )

    @classmethod
    def parse(cls, inputGrammar):
        """
            Parse the regular grammar and return its Abstract Syntax Tree.
        """
        return cls._parser.parse( inputGrammar )

    def __init__(self, initial_symbol="", productions=None):
        # {'1': {( 'a', '' ), ( 'a', 'A' )}}
        self.productions = productions if productions else {}
        self.initial_symbol = initial_symbol

        self.non_terminal_counter = 0
        self.generated_non_terminals = DynamicIterationSet()
        self.last_non_terminal_length = 0

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
        AST = cls.parse( "\n".join( getCleanSpaces( input_text_form ) ) )
        log( 4, "\n%s", AST.pretty() )

        # initial_symbol: 1
        # productions:    {'1': {'b', 'a2', 'b2', 'a'}, '2': {'b', 'a2', 'b2', 'a'}}
        productions = {}
        initial_symbol = ''

        # S -> a S | a | b S
        current_level = ''

        def parse_tree(tree, level, children_count):
            level_name = tree.data

            nonlocal productions
            nonlocal current_level
            nonlocal initial_symbol

            for node in tree.children:

                if isinstance( node, lark.Tree ):
                    log( 4, "level: %s, level_name: %-15s children_count: %s", level, level_name, children_count )
                    parse_tree( node, level+1, len( node.children ) )

                else:
                    log( 4, "level: %s, level_name: %-15s node: %-15s current_level: %s", level, level_name, node, current_level )

                    if level_name == 'productions':

                        if level == 0:
                            current_level = node

                            if len( initial_symbol ) == 0:
                                initial_symbol = current_level

                    if level_name == 'non_terminals':

                        if current_level not in productions:
                            productions[current_level] = set()

                        productions[current_level].add( node )

        new_tree = RegularGrammarTreeTransformer().transform( AST )
        parse_tree( new_tree, 0, len( new_tree.children ) )
        grammar = RegularGrammar( initial_symbol, productions )

        log( 4, "\n%s", new_tree.pretty() )
        log( 4, "Result initial_symbol: %s", initial_symbol )
        log( 4, "Result productions:    %s", productions )
        log( 4, "Result grammar:        %s", grammar )
        return grammar

