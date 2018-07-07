#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark

grammar_file_path = "../source/grammar_parser.lark"

with open( grammar_file_path, "r", encoding='utf-8' ) as file:
    _parser = lark.Lark( file.read(), start='grammar', parser='lalr' )

# _parser = lark.Lark.open( "../source/grammar_parser.lark", start='grammar', parser='lalr' )
# """, start='grammar', parser='earley', ambiguity="explicit" )

tree = _parser.parse( "S -> S SS | &" )
# tree = _parser.parse( "S -> a & 1)\" | aa S1 a SS AAA  |  B  |  C  a\nB -> BB\nC -> CC" )
# tree = _parser.parse( "S SS -> AA BBBB | EEE\nC -> CC\nD-> DD DDD" )
print( tree.pretty() )

