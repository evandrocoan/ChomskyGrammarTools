#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import lark

from debug_tools import getLogger

from .production import Production

from .symbols import Terminal
from .symbols import NonTerminal

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, os.path.basename( os.path.dirname( os.path.abspath ( __file__ ) ) ) )


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

    def non_terminal_start(self, non_terminal):
        log( 4, 'non_terminal: %s', non_terminal )
        new_production = Production( -1 )
        new_production.add( non_terminal[0] )
        return new_production

    def terminal(self, _terminals):
        return self._parse_symbols( _terminals, Terminal )

    def non_terminal(self, _non_terminals):
        return self._parse_symbols( _non_terminals, NonTerminal )

    def epsilon(self, _terminal):
        return self._parse_symbol( _terminal, '&' )

    def quote(self, _terminal):
        return self._parse_symbol( _terminal, "'" )

    def dash_phi_hyphen(self, _terminal):
        return self._parse_symbol( _terminal, "-" )

    def plus(self, _terminal):
        return self._parse_symbol( _terminal, "+" )

    def star(self, _terminal):
        return self._parse_symbol( _terminal, "*" )

    def open_paren(self, _terminal):
        return self._parse_symbol( _terminal, "(" )

    def close_paren(self, _terminal):
        return self._parse_symbol( _terminal, ")" )

    def _parse_symbol(self, _terminal, default):

        if len( _terminal ):
            return Terminal( _terminal )

        return Terminal( default )

    def _parse_symbols(self, _symbols, Type):
        log( 4, 'productions: %s, type: %s', _symbols, Type )
        results = []

        for _symbol in _symbols:
            results.append( str( _symbol ) )

        symbol = Type( "".join( results ) )
        log( 4, "results: %s", results )
        log( 4, "symbol:  %s", symbol )
        return symbol

    def production(self, productions):
        log( 4, 'productions: %s', productions )
        new_production = Production()

        for production in productions:

            if isinstance( production, ( Terminal, NonTerminal ) ):
                new_production.add( production )

        log( 4, "new_production: %s", new_production )
        return new_production

