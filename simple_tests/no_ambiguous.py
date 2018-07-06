#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark

_parser = lark.Lark( r"""
        grammar      : start_symbol "->" production
        start_symbol : WHITE_SPACE* production_symbols+

        production  : WHITE_SPACE* production_symbols+ "|" production
                    | WHITE_SPACE* production_symbols+

        production_symbols   : terminals_begin | non_terminals_begin
        terminal_symbols     : LOW_CASE_LETTER
        non_terminal_symbols : UPPER_CASE_LETTER

        non_terminals_begin : non_terminal_symbols non_terminals_end
        non_terminals_end   : non_terminal_symbols non_terminals_end | white_space+ | UPPER_CASE_LETTER2

        terminals_begin : terminal_symbols terminals_end
        terminals_end   : terminal_symbols terminals_end | white_space+ | LOW_CASE_LETTER2

        LOW_CASE_LETTER  : /[a-zØ-öø-ÿ]/
        LOW_CASE_LETTER2 : /[a-zØ-öø-ÿ]$/

        UPPER_CASE_LETTER  : /[A-ZÀ-Ö]/
        UPPER_CASE_LETTER2 : /[A-ZÀ-Ö]$/

        // Common definitions
        WHITE_SPACE : ( " " | /\t/ )
        ?white_space : WHITE_SPACE
""", start='grammar', parser='lalr' )
# """, start='grammar', parser='earley', ambiguity="explicit" )

tree = _parser.parse( "S -> a | S SS AAA  |  B  |  C  " )
print( tree.pretty() )

