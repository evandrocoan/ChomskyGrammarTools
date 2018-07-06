#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark

_parser = lark.Lark( r"""
        grammar      : start_symbol "->" production
        start_symbol : WHITE_SPACE* symbols_begin

        production  : WHITE_SPACE* symbols_begin "|" production
                    | WHITE_SPACE* symbols_begin

        grammar_symbols      : non_terminals_begin
        non_terminal_symbols : UPPER_CASE_LETTER

        symbols_begin : grammar_symbols symbols_end
        symbols_end   : grammar_symbols symbols_end | []

        non_terminals_begin : non_terminal_symbols non_terminals_end
        non_terminals_end   : non_terminal_symbols non_terminals_end | white_space+ | UPPER_CASE_LETTER2

        UPPER_CASE_LETTER  : /[A-ZÀ-Ö]/
        UPPER_CASE_LETTER2 : /[A-ZÀ-Ö]$/

        // Common definitions
        WHITE_SPACE : ( " " | /\t/ )
        ?white_space : WHITE_SPACE
""", start='grammar', parser='earley', ambiguity="explicit" )
# """, start='grammar', parser='lalr' )

tree = _parser.parse( "S -> S SS AAA  |  B  |  C  " )
print( tree.pretty() )

