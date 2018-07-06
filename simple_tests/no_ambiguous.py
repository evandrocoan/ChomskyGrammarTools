#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark

_parser = lark.Lark( r"""
        start        : start_symbol "->" productions
        start_symbol : white_spaces symbols white_spaces

        productions  : white_spaces symbols white_spaces productions | symbols

        symbols  : UPPER_CASE_LETTER symbols2
        ?symbols2 : UPPER_CASE_LETTER symbols2 | WHITE_SPACE | UPPER_CASE_LETTER2

        UPPER_CASE_LETTER  : /[A-ZÀ-Ö]/
        UPPER_CASE_LETTER2 : /[A-ZÀ-Ö]$/

        // Common definitions
        WHITE_SPACE  : ( " " | /\t/ )
        white_space  : WHITE_SPACE
        white_spaces : WHITE_SPACE white_spaces | []
""", start='start', parser='earley', ambiguity="explicit" )

tree = _parser.parse( "S -> S SS SSS AAA" )
print( tree.pretty() )

