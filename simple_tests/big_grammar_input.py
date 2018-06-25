#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pstats

import profile
import cProfile

from io import StringIO

cur_path = os.path.join( os.getcwd(), '..', 'source' )
sys.path.append( cur_path )

from grammar.grammar import ChomskyGrammar
from grammar.utilities import wrap_text

arg = r"""
    S -> a A | a
    A -> b S1 | b
    S1 -> b S2 | b
    S2 -> b S3 | b
    S3 -> b S4 | b
    S4 -> b S5 | b
    S5 -> b S6 | b
    S6 -> b S7 | b
    S7 -> b S8 | b
    S8 -> b S9 | b
    S9 -> b S10 | b
    S10 -> b S11 | b
    S11 -> b S12 | b
    S12 -> b S13 | b
    S13 -> b S14 | b
    S14 -> b S15 | b
    S15 -> b S16 | b
    S16 -> b S17 | b
    S17 -> b S18 | b
    S18 -> b S19 | b
    S19 -> b S20 | b
    S20 -> b S21 | b
    S21 -> b S22 | b
    S22 -> b S23 | b
    S23 -> b S24 | b
    S24 -> b S25 | b
    S25 -> b S26 | b
    S26 -> b S27 | b
    S27 -> b S28 | b
    S28 -> b S29 | b
    S29 -> b S30 | b
    S30 -> b S31 | b
    S31 -> b S32 | b
    S32 -> b S33 | b
    S33 -> b S34 | b
    S34 -> b S35 | b
    S35 -> b S36 | b
    S36 -> b S37 | b
    S37 -> b S38 | b
    S38 -> b S39 | b
    S39 -> b S40 | b
    S40 -> b S41 | b
    S41 -> b S42 | b
    S42 -> b S43 | b
    S43 -> b S44 | b
    S44 -> b S45 | b
    S45 -> b S46 | b
    S46 -> b S47 | b
    S47 -> b S48 | b
    S48 -> b S49 | b
    S49 -> b S50 | b
    S50 -> b S51 | b
    S51 -> b S52 | b
    S52 -> b S53 | b
    S53 -> b S54 | b
    S54 -> b S55 | b
    S55 -> b S56 | b
    S56 -> b S57 | b
    S57 -> b S58 | b
    S58 -> b S59 | b
    S59 -> b S60 | b
    S60 -> b S61 | b
    S61 -> b S62 | b
    S62 -> b S63 | b
    S63 -> b S64 | b
    S64 -> b S65 | b
    S65 -> b S66 | b
    S66 -> b S67 | b
    S67 -> b S68 | b
    S68 -> b S69 | b
    S69 -> b S70 | b
    S70 -> b S71 | b
    S71 -> b S72 | b
    S72 -> b S73 | b
    S73 -> b S74 | b
    S74 -> b S75 | b
    S75 -> b S76 | b
    S76 -> b S77 | b
    S77 -> b S78 | b
    S78 -> b S79 | b
    S79 -> b S80 | b
    S80 -> b S81 | b
    S81 -> b S82 | b
    S82 -> b S83 | b
    S83 -> b S84 | b
    S84 -> b S85 | b
    S85 -> b S86 | b
    S86 -> b S87 | b
    S87 -> b S88 | b
    S88 -> b S89 | b
    S89 -> b S90 | b
    S90 -> b S91 | b
    S91 -> b S92 | b
    S92 -> b S93 | b
    S93 -> b S93 | b
"""

"""

profiling a method of a class in Python using cProfile?
https://stackoverflow.com/questions/4492535/profiling-a-method-of-a-class-in-python-using-cprofile

Python getting meaningful results from cProfile
https://stackoverflow.com/questions/21274898/python-getting-meaningful-results-from-cprofile

"""

# cProfile.runctx( "firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text( arg ) )", globals(), locals(), sort='time' )
# cProfile.runctx( "firstGrammar.is_factored()", globals(), locals(), sort='time' )

profiller = cProfile.Profile()
profiller.enable()


# firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text( "S -> S" ) )
firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text( arg ) )


profiller.disable()
output_stream = StringIO()

profiller_status = pstats.Stats( profiller, stream=output_stream )
profiller_status.sort_stats( "time" )
profiller_status.print_stats()

print( output_stream.getvalue() )


