#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# Licensing
#
# Chomsky Grammar Input Tree Transformer
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
import lark

from lark import Tree
from debug_tools import getLogger

from .production import Production

from .symbols import Terminal
from .symbols import NonTerminal

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, __name__ )


# S -> a A | a
#
# productions
#   non_terminal_start
#     non_terminal    S
#   non_terminals
#     production
#       terminal  a
#       non_terminal  A
#     production
#       terminal  a
#   end_symbol
class ChomskyGrammarTreeTransformer(lark.Transformer):
    """
        Transforms the AST (Abstract Syntax Tree) nodes into meaningful string representations,
        allowing simple recursive parsing parsing of the AST tree.

        Tree(
                productions,
                [
                   Tree( non_terminal, [Token( UCASE_LETTER, 'S' )] ),
                   Tree(
                           non_terminals,
                           [
                               Tree( production, [Tree( terminal, [Token( LCASE_LETTER, 'a' )] ), Tree( non_terminal, [Token( UCASE_LETTER, 'A' )] )] ),
                               Tree( production, [Tree( terminal, [Token( LCASE_LETTER, 'a' )] )] )
                           ]
                        )
                ]
            )
    """

    def start_symbol(self, productions):
        """
            Converts the tree start symbol into a production ready to be used in the Chomsky Grammar.
        """
        log( 4, 'productions: %s', productions )
        return productions[0]

    def terminals(self, _terminals):
        """
            Converts the tree leaf terminal into a Terminal ready to be used in the Chomsky Grammar.
        """
        return self._parse_symbols( _terminals, Terminal )

    def non_terminals(self, _non_terminals):
        """
            Converts the tree leaf non terminal symbol into a NonTerminal ready to be used in the Chomsky Grammar.
        """
        return self._parse_symbols( _non_terminals, NonTerminal )

    def _parse_symbols(self, symbols, Type):
        log( 4, 'productions: %s, type: %s', symbols, Type )
        results = []

        for symbol in symbols:
            results.append( str( symbol ) )

        symbol = Type( "".join( results ) )
        log( 4, "results: %s %s", results, symbol.repr() )
        return symbol

    def production(self, tokens):
        """
            Converts the tree leaf Terminal's and NonTerminal's symbols into a production ready to
            be used in the Chomsky Grammar.
        """
        log( 4, 'tokens: %s', tokens )
        new_production = Production()

        for element in tokens:

            if isinstance( element, Tree ):
                symbol = element.children[0]

                if isinstance( symbol, ( Terminal, NonTerminal ) ):
                    new_production.add( symbol )

        log( 4, "new_production: %s", new_production.repr() )
        return new_production

