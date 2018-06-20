#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import lark
import unittest

from natsort import natsorted
from collections import OrderedDict
from debug_tools import getLogger

from grammar.grammar import ChomskyGrammar
from grammar.utilities import wrap_text
from grammar.utilities import getCleanSpaces
from grammar.utilities import sort_correctly
from grammar.utilities import dictionary_to_string
from grammar.utilities import convert_to_text_lines
from grammar.utilities import get_duplicated_elements
from grammar.utilities import sort_alphabetically_and_by_length

from grammar.symbols import Terminal
from grammar.symbols import NonTerminal

from grammar.production import Production
from grammar.production import epsilon_production
from grammar.production import epsilon_terminal

from grammar.lockable_type import LockableType
from grammar.tree_transformer import ChomskyGrammarTreeTransformer
from grammar.testing_utilities import TestingUtilities

log = getLogger( 127, os.path.basename( os.path.dirname( os.path.abspath ( __file__ ) ) ) )
log( 1, "Importing " + __name__ )


class TestChomskyGrammar(TestingUtilities):

    def test_grammarProductionsDictionaryKeyError(self):
        LockableType._USE_STRING = False

        non_terminal_A = NonTerminal( 'A' )
        production_A = Production( [non_terminal_A], True )

        # print( "production_A:", hash( production_A ) )
        # print( "non_terminal_A:", hash( non_terminal_A ) )

        dictionary = {}
        dictionary[production_A] = 'cow'

        self.assertTextEqual(
        """
            cow
        """, dictionary[non_terminal_A] )

    def test_grammarInvalidNonTerminalException(self):

        with self.assertRaisesRegex( RuntimeError, "Invalid Non Terminal `D` added to the grammar" ):
            firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
            """
                S -> Ab | A Dc
                B -> bB | Ad | &
                A -> aA | &
            """ ) )
            firstGrammar.assure_existing_symbols()

    def test_grammarEpsilonProductionEvalutesTrueOnIf(self):

        if epsilon_production:
            self.fail( "Epsilon production did evaluate to `True`" )

        if epsilon_terminal:
            self.fail( "Epsilon terminal did evaluate to `True`" )

        if Production( symbols=[Terminal( "&" )], lock=True ):
            self.fail( "Recent created Epsilon Production did not evaluate to `True`" )

        if not Terminal( "a", lock=True ):
            self.fail( "Terminal did not evaluate to `True`" )

        if not NonTerminal( "A", lock=True ):
            self.fail( "NonTerminal did not evaluate to `True`" )

        if not Production( symbols=[Terminal( "b" )], lock=True ):
            self.fail( "Production did not evaluate to `True`" )

    def test_grammarNonTerminalHasProductionChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        terminal_b = Terminal( "b" )
        non_terminal_S = NonTerminal( "S" )
        non_terminal_A = NonTerminal( "A" )

        production_S = Production( symbols=[non_terminal_S], lock=True )
        production_A = Production( symbols=[non_terminal_A, terminal_b], lock=True )

        self.assertFalse( firstGrammar.has_production( non_terminal_S, production_S ) )
        self.assertTrue( firstGrammar.has_production( non_terminal_S, production_A ) )

    def test_grammarRemovingInitialSymbolChapter5Example1FirstMutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> S
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        firstGrammar.remove_production( firstGrammar.initial_symbol, firstGrammar.initial_symbol )

        self.assertTextEqual(
        """
            + S' -> S'
            +  A -> & | a A
            +  B -> & | A d | b B
        """, firstGrammar )

    def test_grammarHasRecursionOnNonTerminalChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        non_terminal_S = NonTerminal( "S", lock=True )
        non_terminal_A = NonTerminal( "A", lock=True )

        self.assertFalse( firstGrammar.has_recursion_on_the_non_terminal( non_terminal_S ) )
        self.assertTrue( firstGrammar.has_recursion_on_the_non_terminal( non_terminal_A ) )

    def test_grammarIsEmptyStoS(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> B
            B -> B
        """ ) )

        self.assertTrue( firstGrammar.is_empty() )

    def test_grammarIsEmptyStoSorEpsilon(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> S | &
        """ ) )

        self.assertFalse( firstGrammar.is_empty() )

    def test_grammarIsFiniteStoS(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> B
            B -> B
        """ ) )

        self.assertFalse( firstGrammar.is_finite() )

    def test_grammarIsFiniteStoSorEpsilon(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> S | &
        """ ) )

        self.assertTrue( firstGrammar.is_finite() )

    def test_grammarIsInfiniteStoS(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> B
            B -> B
        """ ) )

        self.assertFalse( firstGrammar.is_infinite() )

    def test_grammarIsInfiniteStoSorEpsilon(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> aS | &
        """ ) )

        self.assertTrue( firstGrammar.is_infinite() )


class TestGrammarEpsilonConversion(TestingUtilities):

    def test_grammarConvertToEpsilonFreeChapter4Item4Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A B
            A -> aA | &
            B -> bB | &
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        """
            + S -> & | A | B | A B
            + A -> a | a A
            + B -> b | b B
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarConvertToEpsilonFreeChapter4Item4Example1Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A B | S S
            A -> aA | &
            B -> bB | &
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        """
            + S' -> & | A | B | A B | S S
            +  A -> a | a A
            +  B -> b | b B
            +  S -> A | B | A B | S S
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarConvertToEpsilonFreeChapter4Item4Example2Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> c S c | B a
            A -> aA | A B C | &
            B -> bB | C A | &
            C -> c C c | A S
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        """
            + S -> a | B a | c S c
            + A -> a | C | a A | A C | B C | A B C
            + B -> b | C | b B | C A
            + C -> S | A S | c C c
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarConvertToEpsilonFreeChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        """
            + S -> b | c | A b | A c | B c | A B c
            + A -> a | a A
            + B -> b | d | A d | b B
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarConvertToEpsilonFreeWithNewInitialSymbolChapter5Example1FirstMutatedWithEpsilonS(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc | A B S | &
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        """
            + S' -> & | b | c | A | B | S | A b | A c | B c | A B | A S | B S | A B c | A B S
            +  A -> a | a A
            +  B -> b | d | A d | b B
            +  S -> b | c | A | B | S | A b | A c | B c | A B | A S | B S | A B c | A B S
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarConvertToEpsilonFreeWithNewInitialSymbolChapter5Example1FirstMutatedS(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc | A B S
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        """
            + S -> b | c | S | A b | A c | B c | A S | B S | A B c | A B S
            + A -> a | a A
            + B -> b | d | A d | b B
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarConvertToEpsilonFreeWithNewInitialSymbolChapter5Example1FirstMutatedNoS(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc | A B
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        """
            + S -> & | b | c | A | B | A b | A c | B c | A B | A B c
            + A -> a | a A
            + B -> b | d | A d | b B
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarGetNonTerminalEpsilonSimpleCaseChapter5Example1First(self):
        LockableType._USE_STRING = False
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: A, symbols: [NonTerminal locked: True, str: A, sequence: 1, len: 1;],
            + sequence: 1, len: 1;
            + , Production locked: True, str: B, symbols: [NonTerminal locked: True, str: B, sequence: 1, len:
            + 1;], sequence: 1, len: 1;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( firstGrammar.get_non_terminal_epsilon() ), wrap=100 ) )

    def test_grammarGetNonTerminalEpsilonChapter5Example1FirstMutated(self):
        LockableType._USE_STRING = False
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc | A B
            A -> aA | &
            B -> bB | Ad | &
        """ ) )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: A, symbols: [NonTerminal locked: True, str: A, sequence: 1, len: 1;],
            + sequence: 1, len: 1;
            + , Production locked: True, str: B, symbols: [NonTerminal locked: True, str: B, sequence: 1, len:
            + 1;], sequence: 1, len: 1;
            + , Production locked: True, str: S, symbols: [NonTerminal locked: True, str: S, sequence: 1, len:
            + 1;], sequence: 1, len: 1;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( firstGrammar.get_non_terminal_epsilon() ), wrap=100 ) )

    def test_grammarIsNotEpsilonFreeChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )

        self.assertFalse( firstGrammar.is_epsilon_free() )

    def test_grammarIsEpsilonFreeChapter5Example1FirstEpsilonFreed(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc | &
            A -> aA | a
            B -> bB | Ad
        """ ) )

        self.assertTrue( firstGrammar.is_epsilon_free() )


class TestGrammarFertileSymbols(TestingUtilities):

    def setUp(self):
        super().setUp()
        LockableType._USE_STRING = False

    def test_grammarFertileNonTerminalsChapter5Example1Follow(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A B C
            A -> aA | &
            B -> bB | A Cd
            C -> cC | &
        """ ) )
        fertile = firstGrammar.fertile()

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: A, symbols: [NonTerminal locked: True, str: A, sequence: 1, len: 1;], sequence: 1, len: 1;
            + , Production locked: True, str: B, symbols: [NonTerminal locked: True, str: B, sequence: 1, len: 1;], sequence: 1, len: 1;
            + , Production locked: True, str: C, symbols: [NonTerminal locked: True, str: C, sequence: 1, len: 1;], sequence: 1, len: 1;
            + , Production locked: True, str: S, symbols: [NonTerminal locked: True, str: S, sequence: 1, len: 1;], sequence: 1, len: 1;
            + ]
        """, sort_alphabetically_and_by_length( fertile ) )

    def test_grammarFertileNonTerminalsChapter5Example1FollowSadPath(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A B C | B C
            A -> aA
            B -> bB | Cd
            C -> cC | c
        """ ) )
        fertile = firstGrammar.fertile()

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: B, symbols: [NonTerminal locked: True, str: B, sequence: 1, len: 1;], sequence: 1, len: 1;
            + , Production locked: True, str: C, symbols: [NonTerminal locked: True, str: C, sequence: 1, len: 1;], sequence: 1, len: 1;
            + , Production locked: True, str: S, symbols: [NonTerminal locked: True, str: S, sequence: 1, len: 1;], sequence: 1, len: 1;
            + ]
        """, sort_alphabetically_and_by_length( fertile ) )

    def test_grammarFertileNonTerminalsChapter5FollowExample2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            E  -> T E'
            E' -> + T E' | &
            T  -> F T'
            T' -> * F T' | &
            F  -> ( E ) | id
        """ ) )
        fertile = firstGrammar.fertile()

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: E, symbols: [NonTerminal locked: True, str: E, sequence: 1, len: 1;], sequence: 1, len: 1;
            + , Production locked: True, str: F, symbols: [NonTerminal locked: True, str: F, sequence: 1, len: 1;], sequence: 1, len: 1;
            + , Production locked: True, str: T, symbols: [NonTerminal locked: True, str: T, sequence: 1, len: 1;], sequence: 1, len: 1;
            + , Production locked: True, str: E', symbols: [NonTerminal locked: True, str: E', sequence: 1, len: 1;], sequence: 1, len: 1;
            + , Production locked: True, str: T', symbols: [NonTerminal locked: True, str: T', sequence: 1, len: 1;], sequence: 1, len: 1;
            + ]
        """, sort_alphabetically_and_by_length( fertile ) )

    def test_grammarFertileNonTerminalsChapter5FollowExample2SadPath(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            E  -> T E'
            E' -> + T E' | &
            T  -> F T'
            T' -> * F T' | &
            F  -> ( E )
        """ ) )
        fertile = firstGrammar.fertile()

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: E', symbols: [NonTerminal locked: True, str: E', sequence: 1, len: 1;], sequence: 1, len: 1;
            + , Production locked: True, str: T', symbols: [NonTerminal locked: True, str: T', sequence: 1, len: 1;], sequence: 1, len: 1;
            + ]
        """, sort_alphabetically_and_by_length( fertile ) )

    def test_grammarGetFertileNonTerminalsChapter4Item1Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> aS | B C | B D
            A -> cC | A B
            B -> bB | &
            C -> aA | B C
            D -> d D d | c
        """ ) )
        fertile = firstGrammar.fertile()

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: B, symbols: [NonTerminal locked: True, str: B, sequence: 1, len: 1;], sequence: 1, len: 1;
            + , Production locked: True, str: D, symbols: [NonTerminal locked: True, str: D, sequence: 1, len: 1;], sequence: 1, len: 1;
            + , Production locked: True, str: S, symbols: [NonTerminal locked: True, str: S, sequence: 1, len: 1;], sequence: 1, len: 1;
            + ]
        """, sort_alphabetically_and_by_length( fertile ) )

    def test_grammarEliminateNonFertileNonTerminalsChapter4Item1Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> aS | B C | B D
            A -> cC | A B
            B -> bB | &
            C -> aA | B C
            D -> d D d | c
        """ ) )
        firstGrammar.eliminate_infertile()

        self.assertTextEqual(
        """
            + S -> a S | B D
            + B -> & | b B
            + D -> c | d D d
        """, firstGrammar )

    def test_grammarEliminateUnreachableSymbolsChapter4Item1Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> aS | B C | B D
            A -> cC | A B
            B -> bB | &
            C -> aA | B C
            D -> d D d | c
        """ ) )
        firstGrammar.eliminate_unreachable()

        self.assertTextEqual(
        """
            + S -> a S | B C | B D
            + A -> c C | A B
            + B -> & | b B
            + C -> a A | B C
            + D -> c | d D d
        """, firstGrammar )

    def test_grammarGetReachableChapter4Item1Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> aSa | dDd
            A -> aB | Cc | a
            B -> dD | bB | b
            C -> Aa | dD | c
            D -> bbB | d
        """ ) )
        reachable = firstGrammar.reachable()

        self.assertTextEqual(
        """
            + Terminal locked: True, str: a, sequence: 1, len: 1;
            + Terminal locked: True, str: b, sequence: 1, len: 1;
            + Terminal locked: True, str: bb, sequence: 1, len: 2;
            + Terminal locked: True, str: d, sequence: 1, len: 1;
            + NonTerminal locked: True, str: B, sequence: 2, len: 1;
            + NonTerminal locked: True, str: D, sequence: 2, len: 1;
            + NonTerminal locked: True, str: S, sequence: 1, len: 1;
        """, convert_to_text_lines( reachable, sort=sort_correctly ) )

    def test_grammarEliminateUneachableSymbolsChapter4Item1Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> aSa | dDd
            A -> aB | Cc | a
            B -> dD | bB | b
            C -> Aa | dD | c
            D -> bbB | d
        """ ) )
        firstGrammar.eliminate_unreachable()

        self.assertTextEqual(
        """
            + S -> a S a | d D d
            + B -> b | b B | d D
            + D -> d | bb B
        """, firstGrammar )

    def test_grammarEliminateUnusefulSymbolsChapter4Item1Example3(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> a F G | b F d | S a
            A -> a A | &
            B -> c G | a C G
            C -> c B a | c a | &
            D -> d C c | &
            F -> b F d | a C | A b | G A
            G -> B c | B C a
        """ ) )
        firstGrammar.eliminate_unuseful()

        self.assertTextEqual(
        """
            + S -> S a | b F d
            + A -> & | a A
            + C -> & | ca
            + F -> A b | a C | b F d
        """, firstGrammar )

    def test_grammarGetNonTerminalSimpleSymbolsChapter4Item3Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> a F G | b F d | S a
            A -> a A | &
            B -> c G | a C G
            C -> c B a | c a | &
            D -> d C c | &
            F -> b F d | a C | A b | G A
            G -> B c | B C a
        """ ) )
        simple_non_terminals = firstGrammar.get_simple_non_terminals()

        self.assertTextEqual(
        r"""
            + Production locked: True, str: A, symbols: [NonTerminal locked: True, str: A, sequence: 1, len: 1;], sequence: 1, len: 1;
            + Production locked: True, str: B, symbols: [NonTerminal locked: True, str: B, sequence: 1, len: 1;], sequence: 1, len: 1;
            + Production locked: True, str: C, symbols: [NonTerminal locked: True, str: C, sequence: 1, len: 1;], sequence: 1, len: 1;
            + Production locked: True, str: D, symbols: [NonTerminal locked: True, str: D, sequence: 1, len: 1;], sequence: 1, len: 1;
            + Production locked: True, str: F, symbols: [NonTerminal locked: True, str: F, sequence: 1, len: 1;], sequence: 1, len: 1;
            + Production locked: True, str: G, symbols: [NonTerminal locked: True, str: G, sequence: 1, len: 1;], sequence: 1, len: 1;
            + Production locked: True, str: S, symbols: [NonTerminal locked: True, str: S, sequence: 1, len: 1;], sequence: 1, len: 1;
        """, wrap_text( convert_to_text_lines( simple_non_terminals, new_line=False ), wrap=120 ) )


class TestGrammarFactoringAndRecursionSymbols(TestingUtilities):

    def test_grammarGetNonTerminalSimpleSymbolsChapter4Item5Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> F G H
            F -> G | a
            G -> dG | H | a
            H -> c
        """ ) )
        simple_non_terminals = firstGrammar.get_simple_non_terminals()

        self.assertTextEqual(
        """
            + S: S
            + F: F G H
            + G: G H
            + H: H
        """, dictionary_to_string( simple_non_terminals ) )

    def test_grammarGetNonTerminalSimpleSymbolsChapter4Item5Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> a B c D e
            B -> b B | E | F
            D -> d D | F | d
            E -> e E | e
            F -> f F | f
        """ ) )
        simple_non_terminals = firstGrammar.get_simple_non_terminals()

        self.assertTextEqual(
        """
            + S: S
            + B: B E F
            + D: D F
            + E: E
            + F: F
        """, dictionary_to_string( simple_non_terminals ) )

    def test_grammarEliminateNonTerminalSimpleSymbolsChapter4Item5Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> F G H
            F -> G | a
            G -> dG | H | a
            H -> c
        """ ) )
        firstGrammar.eliminate_simple_non_terminals()

        self.assertTextEqual(
        """
            + S -> F G H
            + F -> a | c | d G
            + G -> a | c | d G
            + H -> c
        """, firstGrammar )

    def test_grammarEliminateNonTerminalSimpleSymbolsChapter4Item5Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> a B c D e
            B -> b B | E | F
            D -> d D | F | d
            E -> e E | e
            F -> f F | f
        """ ) )
        firstGrammar.eliminate_simple_non_terminals()

        self.assertTextEqual(
        """
            + S -> a B c D e
            + B -> e | f | b B | e E | f F
            + D -> d | f | d D | f F
            + E -> e | e E
            + F -> f | f F
        """, firstGrammar )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item5Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Sa | b
        """ ) )

        self.assertTextEqual(
        """
            + (S, 'direct')
        """, convert_to_text_lines( firstGrammar.left_recursion() ) )

    def test_grammarEliminateLeftRecursionCalculationOfChapter5Item5Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Sa | b
        """ ) )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        """
            +  S -> b S'
            + S' -> & | a S'
        """, firstGrammar )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item5Example1Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> aSa | b
        """ ) )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item5Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            E -> E + T | T
            T -> T * F | F
            F -> ( E ) | id
        """ ) )

        self.assertTextEqual(
        """
            + (E, 'direct')
            + (T, 'direct')
        """, convert_to_text_lines( firstGrammar.left_recursion() ) )

        self.assertTrue( firstGrammar.has_left_recursion() )

    def test_grammarEliminateLeftRecursionCalculationOfChapter5Item5Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            E -> E + T | T
            F -> ( E ) | id
            T -> T * F | F
        """ ) )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        """
            +  E -> T E'
            +  F -> id | ( E )
            +  T -> id T' | ( E ) T'
            + E' -> & | + T E'
            + T' -> & | * F T'
        """, firstGrammar )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarEliminateLeftRecursionCalculationOfChapter5Item5Example2WithoutSimpleTerminals(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            E -> E + T | T
            T -> T * F | F
            F -> ( E ) | id
        """ ) )
        firstGrammar.eliminate_simple_non_terminals()

        self.assertTextEqual(
        """
            + E -> id | ( E ) | E + T | T * F
            + F -> id | ( E )
            + T -> id | ( E ) | T * F
        """, firstGrammar )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        """
            +  E -> id E' | ( E ) E' | T * F E'
            +  F -> id | ( E )
            +  T -> id T' | ( E ) T'
            + E' -> & | + T E'
            + T' -> & | * F T'
        """, firstGrammar )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item5Example2Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            E -> a E + T | T
            T -> b T * T | F
            F -> ( E ) | id
        """ ) )

        self.assertFalse( firstGrammar.has_left_recursion() )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        """
            + E -> T | a E + T
            + F -> id | ( E )
            + T -> F | b T * T
        """, firstGrammar )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item6Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Aa | Sb
            A -> Sc | d
        """ ) )

        self.assertTextEqual(
        """
            + (A, 'indirect')
            + (S, 'direct')
        """, convert_to_text_lines( firstGrammar.left_recursion(), sort=sort_correctly ) )

        self.assertTrue( firstGrammar.has_left_recursion() )

    def test_grammarEliminateLeftRecursionOfChapter5Item6Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Aa | Sb
            A -> Sc | d
        """ ) )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        """
            +  S -> A a S'
            +  A -> d A'
            + A' -> & | a S' c A'
            + S' -> & | b S'
        """, firstGrammar )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item6Example1Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> aAa | bSb
            A -> Sc | d
        """ ) )

        self.assertFalse( firstGrammar.has_left_recursion() )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        """
            + S -> a A a | b S b
            + A -> d | S c
        """, firstGrammar )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item6Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> aS | Ab
            A -> Ab | Bc | a
            B -> Bd | Sa | e
        """ ) )

        self.assertTextEqual(
        """
            + (A, 'direct')
            + (B, 'direct')
            + (S, 'indirect')
        """, convert_to_text_lines( firstGrammar.left_recursion() ) )

        self.assertTrue( firstGrammar.has_left_recursion() )

    def test_grammarEliminateLeftRecursionCalculationOfChapter5Item6Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> aS | Ab
            A -> Ab | Bc | a
            B -> Bd | Sa | e
        """ ) )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        """
            +  S -> A b | a S
            +  A -> a A' | B c A'
            +  B -> e B' | a S a B' | a A' ba B'
            + A' -> & | b A'
            + B' -> & | d B' | c A' ba B'
        """, firstGrammar )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item6Example2Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> aS | aAb
            A -> aAb | bBc | a
            B -> bBd | aSa | e
        """ ) )

        self.assertFalse( firstGrammar.has_left_recursion() )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        """
            + S -> a S | a A b
            + A -> a | a A b | b B c
            + B -> e | a S a | b B d
        """, firstGrammar )

    def test_grammarEliminateLeftRecursionCalculationOfExercise6List3ItemC(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Bd | &
            A -> Sa | &
            B -> Ab | Bc
        """ ) )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        """
            +  S' -> & | B d
            +   A -> a | S a
            +   B -> b B' | ab B' | S ab B'
            +   S -> b B' d S'' | ab B' d S''
            +  B' -> & | c B'
            + S'' -> & | ab B' d S''
        """, firstGrammar )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarConvertToProperCalculationOfExercise6List3ItemC(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Bd | &
            A -> Sa | &
            B -> Ab | Bc
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        """
            + S' -> & | B d
            +  A -> a | S a
            +  B -> b | A b | B c
            +  S -> B d
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarIsFactoredCalculationOfChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )

        self.assertTextEqual(
        """
            + (A, a)
            + (B, a)
            + (B, b)
            + (B, d)
            + (S, a)
            + (S, a)
            + (S, a)
            + (S, b)
            + (S, b)
            + (S, c)
            + (S, d)
            + (A, &)
            + (B, &)
        """, convert_to_text_lines( firstGrammar.factors(), sort=sort_correctly ) )

        self.assertFalse( firstGrammar.is_factored() )

    def test_grammarFactoringOfChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        factor_it = firstGrammar.factor_it(3)

        self.assertTextEqual(
        """
            +  S -> c | dc | a S1 | b S2
            +  A -> & | a A
            +  B -> & | d | b B | a A d
            + S1 -> c | dc | a S3 | b S4
            + S2 -> & | c | dc | b B c | a A dc
            + S3 -> c | dc | a S5 | b S6
            + S4 -> & | c | dc | b B c | a A dc
            + S5 -> b | c | dc | a A b | b B c | a A dc | a A B c
            + S6 -> & | c | dc | b B c | a A dc
        """, firstGrammar )

        self.assertTextEqual(
        """
            + (S5, a)
            + (S5, b)
        """, convert_to_text_lines( get_duplicated_elements( firstGrammar.factors() ) ) )

        self.assertFalse( factor_it )
        self.assertFalse( firstGrammar.is_factored() )

    def test_grammarFactoringOfList3Exercice7ItemA(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            P -> D L | &
            C -> V=exp | id (E)
            D -> d D | &
            E -> exp, E | exp
            L -> L; C | C
            V -> id[E] | id
        """ ) )

        self.assertTextEqual(
        """
            + P -> & | D L
            + C -> V =exp | id( E )
            + D -> & | d D
            + E -> exp | exp, E
            + L -> C | L ; C
            + V -> id | id[ E ]
        """, firstGrammar )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        """
            +  P -> & | L | D L
            +  C -> V =exp | id( E )
            +  D -> d | d D
            +  E -> exp | exp, E
            +  L -> V =exp L' | id( E ) L'
            +  V -> id | id[ E ]
            + L' -> & | ; C L'
        """, firstGrammar )
        factor_it = firstGrammar.factor_it(5)

        self.assertTextEqual(
        """
            +  P -> & | d P1 | i P2
            +  C -> i C1
            +  D -> d D1
            +  E -> e E1
            +  L -> i L1
            +  V -> i V1
            + C1 -> d C2
            + C2 -> =exp | ( E ) | [ E ]=exp
            + D1 -> & | d D1
            + E1 -> x E2
            + E2 -> p E3
            + E3 -> & | , E
            + L1 -> d L2
            + L2 -> =exp L' | ( E ) L' | [ E ]=exp L'
            + L' -> & | ; C L'
            + P1 -> i L1 | d D1 L
            + P2 -> d P3
            + P3 -> =exp L' | ( E ) L' | [ E ]=exp L'
            + V1 -> d V2
            + V2 -> & | [ E ]
        """, firstGrammar )

        self.assertTrue( factor_it )
        self.assertTrue( firstGrammar.is_factored() )
        self.assertTextEqual( "", convert_to_text_lines( get_duplicated_elements( firstGrammar.factors() ) ) )


class TestGrammarTreeParsing(TestingUtilities):

    def test_grammarTreeParsingComplexSingleProduction(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        """
            S -> aABbbCC1aAbA BC | ba | c
        """ ) )

        self.assertTextEqual(
        """
            + productions
            +   non_terminal_start
            +     non_terminal  S
            +   space
            +   non_terminals
            +     production
            +       space
            +       terminal  a
            +       non_terminal
            +         A
            +         B
            +       terminal
            +         b
            +         b
            +       non_terminal
            +         C
            +         C
            +       terminal
            +         1
            +         a
            +       non_terminal  A
            +       terminal  b
            +       non_terminal  A
            +       space
            +       non_terminal
            +         B
            +         C
            +       space
            +     production
            +       space
            +       terminal
            +         b
            +         a
            +       space
            +     production
            +       space
            +       terminal  c
        """, firstGrammar.pretty() )

    def test_grammarInputParsingComplexSingleProduction(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines(
        """
            S  -> aABbbCC1aAbA BC | ba | c
            A  -> &
            AB -> &
            BC -> &
            CC -> &
        """ )

        self.assertTextEqual(
        """
            +  S -> c | ba | a AB bb CC 1a A b A BC
            +  A -> &
            + AB -> &
            + BC -> &
            + CC -> &
        """, firstGrammar )

    def test_grammarInputParsingSymbolMerging(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines(
        """
            S -> a b cd | AccD | Ac cD
            A -> &
            D -> &
        """ )

        self.assertTextEqual(
        """
            + S -> abcd | A cc D
            + A -> &
            + D -> &
        """, str( firstGrammar ) )

    def test_grammarTreeParsingABandB(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        """
            S -> aABb BC | b
        """ ) )

        self.assertTextEqual(
        """
            + productions
            +   non_terminal_start
            +     non_terminal  S
            +   space
            +   non_terminals
            +     production
            +       space
            +       terminal  a
            +       non_terminal
            +         A
            +         B
            +       terminal  b
            +       space
            +       non_terminal
            +         B
            +         C
            +       space
            +     production
            +       space
            +       terminal  b
        """, firstGrammar.pretty() )

    def test_grammarInputParsingEmptyEpsilon(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines(
        """
             S ->
            SS -> S |
        """ )

        self.assertTextEqual(
        """
            +  S -> &
            + SS -> & | S
        """, str( firstGrammar ) )

    def test_grammarTreeParsingEmptyEpsilon(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        """
             S ->
            SS -> S |
        """ ) )

        self.assertTextEqual(
        """
            + productions
            +   space
            +   non_terminal_start
            +     non_terminal  S
            +   space
            +   non_terminals
            +     production
            +       epsilon
            +   end_symbol
            +     new_line
            +
            +   non_terminal_start
            +     non_terminal
            +       S
            +       S
            +   space
            +   non_terminals
            +     production
            +       space
            +       non_terminal  S
            +       space
            +     production
            +       epsilon
        """, firstGrammar.pretty() )

    def test_grammarInputParsingSSandEpsilon(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines(
        """
            S   -> SS SSS | &
            SS  -> &
            SSS -> &
        """ )

        self.assertTextEqual(
        """
            +   S -> & | SS SSS
            +  SS -> &
            + SSS -> &
        """, str( firstGrammar ) )

    def test_grammarTreeParsingSSandEpsilon(self):
        firstGrammar = ChomskyGrammar.parse(
        """
            S -> S SS | &
        """ )

        self.assertTextEqual(
        """
            + productions
            +   new_line
            +
            +   space
            +   space
            +   space
            +   space
            +   space
            +   space
            +   space
            +   space
            +   space
            +   space
            +   space
            +   space
            +   non_terminal_start
            +     non_terminal  S
            +   space
            +   non_terminals
            +     production
            +       space
            +       non_terminal  S
            +       space
            +       non_terminal
            +         S
            +         S
            +       space
            +     production
            +       space
            +       epsilon
            +   end_symbol
            +     new_line
            +
            +     space
            +     space
            +     space
            +     space
            +     space
            +     space
            +     space
            +     space
        """, firstGrammar.pretty() )

    def test_grammarSingleAmbiguityCase(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        """
            S -> S S | &
        """ ) )

        self.assertTextEqual(
        """
            + productions
            +   non_terminal_start
            +     non_terminal  S
            +   space
            +   non_terminals
            +     production
            +       space
            +       non_terminal  S
            +       space
            +       non_terminal  S
            +       space
            +     production
            +       space
            +       epsilon
        """, firstGrammar.pretty() )


class TestGrammarTreeTransformation(TestingUtilities):

    def setUp(self):
        super().setUp()
        LockableType._USE_STRING = False

    def test_grammarTransformationTreeParsingParenStarPlusSymbols(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        """
            E  -> T E'
            E' -> + T E' | &
            T  -> F T'
            T' -> * F T'
            F  -> ( E ) | id
        """ ) )
        firstGrammar = ChomskyGrammarTreeTransformer().transform( firstGrammar )

        self.assertTextEqual(
        r"""
            + Tree(productions, [Production locked: False, str: , symbols: [NonTerminal locked: True, str: E,
            + sequence: 1, len: 1;], sequence: 1, len: 0;
            + , Tree(space, []), Tree(space, []), Tree(non_terminals, [Production locked: False, str: , symbols:
            + [NonTerminal locked: True, str: T, sequence: 1, len: 1;, NonTerminal locked: True, str: E',
            + sequence: 2, len: 1;], sequence: 2, len: 0;
            + ]), Tree(end_symbol, [Tree(new_line, [Token(NEWLINE, '\n')])]), Production locked: False, str: ,
            + symbols: [NonTerminal locked: True, str: E', sequence: 1, len: 1;], sequence: 1, len: 0;
            + , Tree(space, []), Tree(non_terminals, [Production locked: False, str: , symbols: [Terminal locked:
            + True, str: +, sequence: 1, len: 1;, NonTerminal locked: True, str: T, sequence: 2, len: 1;,
            + NonTerminal locked: True, str: E', sequence: 3, len: 1;], sequence: 3, len: 0;
            + , Production locked: False, str: , symbols: [Terminal locked: True, str: &, sequence: 1, len: 0;],
            + sequence: 1, len: 0;
            + ]), Tree(end_symbol, [Tree(new_line, [Token(NEWLINE, '\n')])]), Production locked: False, str: ,
            + symbols: [NonTerminal locked: True, str: T, sequence: 1, len: 1;], sequence: 1, len: 0;
            + , Tree(space, []), Tree(space, []), Tree(non_terminals, [Production locked: False, str: , symbols:
            + [NonTerminal locked: True, str: F, sequence: 1, len: 1;, NonTerminal locked: True, str: T',
            + sequence: 2, len: 1;], sequence: 2, len: 0;
            + ]), Tree(end_symbol, [Tree(new_line, [Token(NEWLINE, '\n')])]), Production locked: False, str: ,
            + symbols: [NonTerminal locked: True, str: T', sequence: 1, len: 1;], sequence: 1, len: 0;
            + , Tree(space, []), Tree(non_terminals, [Production locked: False, str: , symbols: [Terminal locked:
            + True, str: *, sequence: 1, len: 1;, NonTerminal locked: True, str: F, sequence: 2, len: 1;,
            + NonTerminal locked: True, str: T', sequence: 3, len: 1;], sequence: 3, len: 0;
            + ]), Tree(end_symbol, [Tree(new_line, [Token(NEWLINE, '\n')])]), Production locked: False, str: ,
            + symbols: [NonTerminal locked: True, str: F, sequence: 1, len: 1;], sequence: 1, len: 0;
            + , Tree(space, []), Tree(space, []), Tree(non_terminals, [Production locked: False, str: , symbols:
            + [Terminal locked: True, str: (, sequence: 1, len: 1;, NonTerminal locked: True, str: E, sequence: 2,
            + len: 1;, Terminal locked: True, str: ), sequence: 3, len: 1;], sequence: 3, len: 0;
            + , Production locked: False, str: , symbols: [Terminal locked: True, str: id, sequence: 1, len: 2;],
            + sequence: 1, len: 0;
            + ])])
        """, wrap_text( firstGrammar, wrap=100 ) )

    def test_grammarTransformationParsingComplexSingleProduction(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        """
            S -> aABbbCC1aAbA BC | ba | c
        """ ) )
        firstGrammar = ChomskyGrammarTreeTransformer().transform( firstGrammar )

        self.assertTextEqual(
        """
            + productions
            +   S
            +   space
            +   non_terminals
            +     a AB bb CC 1a A b A BC
            +     ba
            +     c
        """, firstGrammar.pretty() )

        self.assertTextEqual( wrap_text(
        r"""
            + Tree(productions, [Production locked: False, str: , symbols: [NonTerminal locked: True, str: S,
            + sequence: 1, len: 1;], sequence: 1, len: 0;
            + , Tree(space, []), Tree(non_terminals, [Production locked: False, str: , symbols: [Terminal locked:
            + True, str: a, sequence: 1, len: 1;, NonTerminal locked: True, str: AB, sequence: 2, len: 1;,
            + Terminal locked: True, str: bb, sequence: 3, len: 2;, NonTerminal locked: True, str: CC, sequence:
            + 4, len: 1;, Terminal locked: True, str: 1a, sequence: 5, len: 2;, NonTerminal locked: True, str: A,
            + sequence: 6, len: 1;, Terminal locked: True, str: b, sequence: 7, len: 1;, NonTerminal locked: True,
            + str: A, sequence: 8, len: 1;, NonTerminal locked: True, str: BC, sequence: 9, len: 1;], sequence: 9,
            + len: 0;
            + , Production locked: False, str: , symbols: [Terminal locked: True, str: ba, sequence: 1, len: 2;],
            + sequence: 1, len: 0;
            + , Production locked: False, str: , symbols: [Terminal locked: True, str: c, sequence: 1, len: 1;],
            + sequence: 1, len: 0;
            + ])])
        """ ), wrap_text( str( firstGrammar ), wrap=100 ) )


class TestProduction(TestingUtilities):

    def setUp(self):
        """
            Creates basic non terminal's for usage.
        """
        super().setUp()
        LockableType._USE_STRING = False

        self.ntA = NonTerminal( "A" )
        self.ntB = NonTerminal( "B" )
        self.ntC = NonTerminal( "C" )
        self.ntD = NonTerminal( "D" )

        self.ta = Terminal( "a" )
        self.tb = Terminal( "b" )
        self.tc = Terminal( "c" )
        self.td = Terminal( "d" )

    def test_combinationABCD(self):
        symbols = [self.ntA, self.ntB, self.ntC, self.ntD]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + Production locked: True, str: A B C D, symbols: [NonTerminal locked: True, str: A, sequence: 1, len:
            + 1;, NonTerminal locked: True, str: B, sequence: 2, len: 1;, NonTerminal locked: True, str: C,
            + sequence: 3, len: 1;, NonTerminal locked: True, str: D, sequence: 4, len: 1;], sequence: 4, len: 4;
        """, wrap_text( repr( production ), wrap=100 ) )

    def test_combinationNonTerminalRemovalSymbolFromABCD(self):
        symbols = [self.ntA, self.ntB, self.ntC, self.ntD]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: &, symbols: [Terminal locked: True, str: &, sequence: 1, len: 0;],
            + sequence: 1, len: 0;
            + , Production locked: True, str: A, symbols: [NonTerminal locked: True, str: A, sequence: 1, len:
            + 1;], sequence: 1, len: 1;
            + , Production locked: True, str: B, symbols: [NonTerminal locked: True, str: B, sequence: 1, len:
            + 1;], sequence: 1, len: 1;
            + , Production locked: True, str: C, symbols: [NonTerminal locked: True, str: C, sequence: 1, len:
            + 1;], sequence: 1, len: 1;
            + , Production locked: True, str: D, symbols: [NonTerminal locked: True, str: D, sequence: 1, len:
            + 1;], sequence: 1, len: 1;
            + , Production locked: True, str: A B, symbols: [NonTerminal locked: True, str: A, sequence: 1, len:
            + 1;, NonTerminal locked: True, str: B, sequence: 2, len: 1;], sequence: 2, len: 2;
            + , Production locked: True, str: A C, symbols: [NonTerminal locked: True, str: A, sequence: 1, len:
            + 1;, NonTerminal locked: True, str: C, sequence: 2, len: 1;], sequence: 2, len: 2;
            + , Production locked: True, str: A D, symbols: [NonTerminal locked: True, str: A, sequence: 1, len:
            + 1;, NonTerminal locked: True, str: D, sequence: 2, len: 1;], sequence: 2, len: 2;
            + , Production locked: True, str: B C, symbols: [NonTerminal locked: True, str: B, sequence: 1, len:
            + 1;, NonTerminal locked: True, str: C, sequence: 2, len: 1;], sequence: 2, len: 2;
            + , Production locked: True, str: B D, symbols: [NonTerminal locked: True, str: B, sequence: 1, len:
            + 1;, NonTerminal locked: True, str: D, sequence: 2, len: 1;], sequence: 2, len: 2;
            + , Production locked: True, str: C D, symbols: [NonTerminal locked: True, str: C, sequence: 1, len:
            + 1;, NonTerminal locked: True, str: D, sequence: 2, len: 1;], sequence: 2, len: 2;
            + , Production locked: True, str: A B C, symbols: [NonTerminal locked: True, str: A, sequence: 1, len:
            + 1;, NonTerminal locked: True, str: B, sequence: 2, len: 1;, NonTerminal locked: True, str: C,
            + sequence: 3, len: 1;], sequence: 3, len: 3;
            + , Production locked: True, str: A B D, symbols: [NonTerminal locked: True, str: A, sequence: 1, len:
            + 1;, NonTerminal locked: True, str: B, sequence: 2, len: 1;, NonTerminal locked: True, str: D,
            + sequence: 3, len: 1;], sequence: 3, len: 3;
            + , Production locked: True, str: A C D, symbols: [NonTerminal locked: True, str: A, sequence: 1, len:
            + 1;, NonTerminal locked: True, str: C, sequence: 2, len: 1;, NonTerminal locked: True, str: D,
            + sequence: 3, len: 1;], sequence: 3, len: 3;
            + , Production locked: True, str: B C D, symbols: [NonTerminal locked: True, str: B, sequence: 1, len:
            + 1;, NonTerminal locked: True, str: C, sequence: 2, len: 1;, NonTerminal locked: True, str: D,
            + sequence: 3, len: 1;], sequence: 3, len: 3;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationNonTerminalRemovalSymbolFromABC(self):
        symbols = [self.ntA, self.ntB, self.ntC]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: &, symbols: [Terminal locked: True, str: &, sequence: 1, len: 0;],
            + sequence: 1, len: 0;
            + , Production locked: True, str: A, symbols: [NonTerminal locked: True, str: A, sequence: 1, len:
            + 1;], sequence: 1, len: 1;
            + , Production locked: True, str: B, symbols: [NonTerminal locked: True, str: B, sequence: 1, len:
            + 1;], sequence: 1, len: 1;
            + , Production locked: True, str: C, symbols: [NonTerminal locked: True, str: C, sequence: 1, len:
            + 1;], sequence: 1, len: 1;
            + , Production locked: True, str: A B, symbols: [NonTerminal locked: True, str: A, sequence: 1, len:
            + 1;, NonTerminal locked: True, str: B, sequence: 2, len: 1;], sequence: 2, len: 2;
            + , Production locked: True, str: A C, symbols: [NonTerminal locked: True, str: A, sequence: 1, len:
            + 1;, NonTerminal locked: True, str: C, sequence: 2, len: 1;], sequence: 2, len: 2;
            + , Production locked: True, str: B C, symbols: [NonTerminal locked: True, str: B, sequence: 1, len:
            + 1;, NonTerminal locked: True, str: C, sequence: 2, len: 1;], sequence: 2, len: 2;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationNonTerminalRemovalSymbolFromAB(self):
        symbols = [self.ntA, self.ntB]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: &, symbols: [Terminal locked: True, str: &, sequence: 1, len: 0;],
            + sequence: 1, len: 0;
            + , Production locked: True, str: A, symbols: [NonTerminal locked: True, str: A, sequence: 1, len:
            + 1;], sequence: 1, len: 1;
            + , Production locked: True, str: B, symbols: [NonTerminal locked: True, str: B, sequence: 1, len:
            + 1;], sequence: 1, len: 1;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationNonTerminalRemovalSymbolFromA(self):
        symbols = [self.ntA]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: &, symbols: [Terminal locked: True, str: &, sequence: 1, len: 0;],
            + sequence: 1, len: 0;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationNonTerminalRemovalSymbolFromAa(self):
        symbols = [self.ntA, self.ta]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: a, symbols: [Terminal locked: True, str: a, sequence: 1, len: 1;],
            + sequence: 1, len: 1;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationNonTerminalRemovalSymbolFromBAa(self):
        symbols = [self.ntB, self.ntA, self.ta.new()]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: a, symbols: [Terminal locked: True, str: a, sequence: 1, len: 1;],
            + sequence: 1, len: 1;
            + , Production locked: True, str: A a, symbols: [NonTerminal locked: True, str: A, sequence: 1, len:
            + 1;, Terminal locked: True, str: a, sequence: 2, len: 1;], sequence: 2, len: 2;
            + , Production locked: True, str: B a, symbols: [NonTerminal locked: True, str: B, sequence: 1, len:
            + 1;, Terminal locked: True, str: a, sequence: 2, len: 1;], sequence: 2, len: 2;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationNonTerminalRemovalSymbolFromaAa(self):
        symbols = [self.ta, self.ntA, self.ta.new()]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: aa, symbols: [Terminal locked: True, str: aa, sequence: 1, len: 2;],
            + sequence: 1, len: 2;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationFilterNonTerminalsFromaAa(self):
        symbols = [self.ta, self.ntA, self.ta.new()]
        production = Production( symbols )
        production.filter_non_terminals( symbols, [] )

        self.assertTextEqual(
        r"""
            + [Terminal locked: True, str: aa, sequence: 1, len: 2;]
        """, sort_alphabetically_and_by_length( production ) )

    def test_combinationFilterNonTerminalsFromAa(self):
        symbols = [self.ntA, self.ta]
        production = Production( symbols )
        production.filter_non_terminals( symbols, [] )

        self.assertTextEqual(
        r"""
            + [Terminal locked: True, str: a, sequence: 1, len: 1;]
        """, sort_alphabetically_and_by_length( production ) )


class TestGrammarFirstAndFollow(TestingUtilities):

    def test_grammarNonTerminalFirstCalculationOfChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        first_non_terminals = firstGrammar.first_non_terminals()

        self.assertTextEqual(
        """
            + S: A B
            + A:
            + B: A
        """, dictionary_to_string( first_non_terminals ) )

    def test_grammarFirstCalculationOfChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        first = firstGrammar.first_terminals()

        self.assertTextEqual(
        """
            + S: a b c d
            + A: & a
            + B: & a b d
        """, dictionary_to_string( first ) )

    def test_grammarFollowCalculationOfChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        follow = firstGrammar.follow_terminals()

        self.assertTextEqual(
        """
            + S: $
            + A: $ a b d
            + B: c
        """, dictionary_to_string( follow ) )

    def test_grammarFirstNonTermianlCalculationOfChapter5Example1Follow(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A B C
            A -> aA | &
            B -> bB | A Cd
            C -> cC | &
        """ ) )
        first_non_terminals = firstGrammar.first_non_terminals()

        self.assertTextEqual(
        """
            + S: A B C
            + A:
            + B: A C
            + C:
        """, dictionary_to_string( first_non_terminals ) )

    def test_grammarFirstCalculationOfChapter5Example1Follow(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A B C
            A -> aA | &
            B -> bB | A Cd
            C -> cC | &
        """ ) )
        first = firstGrammar.first_terminals()

        self.assertTextEqual(
        """
            + S: a b c d
            + A: & a
            + B: a b c d
            + C: & c
        """, dictionary_to_string( first ) )

    def test_grammarFollowCalculationOfChapter5Example1Follow(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A B C
            A -> aA | &
            B -> bB | A Cd
            C -> cC | &
        """ ) )
        follow = firstGrammar.follow_terminals()

        self.assertTextEqual(
        """
            + S: $
            + A: $ a b c d
            + B: $ c
            + C: $ d
        """, dictionary_to_string( follow ) )

    def test_grammarFirstCalculationOfChapter5FollowExample2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            E  -> T E'
            E' -> + T E' | &
            T  -> F T'
            T' -> * F T' | &
            F  -> ( E ) | id
        """ ) )
        first = firstGrammar.first_terminals()

        self.assertTextEqual(
        """
            +  E: ( id
            + E': & +
            +  T: ( id
            + T': & *
            +  F: ( id
        """, dictionary_to_string( first ) )

    def test_grammarFirstNonTerminalCalculationOfChapter5FollowExample2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            E  -> T E'
            E' -> + T E' | &
            T  -> F T'
            T' -> * F T' | &
            F  -> ( E ) | id
        """ ) )
        first_non_terminals = firstGrammar.first_non_terminals()

        self.assertTextEqual(
        """
            +  E: F T
            + E':
            +  T: F
            + T':
            +  F:
        """, dictionary_to_string( first_non_terminals ) )

    def test_grammarFollowCalculationOfChapter5FollowExample2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            E  -> T E'
            E' -> + T E' | &
            T  -> F T'
            T' -> * F T' | &
            F  -> ( E ) | id
        """ ) )
        follow = firstGrammar.follow_terminals()

        self.assertTextEqual(
        """
            +  E: $ )
            + E': $ )
            +  T: $ ) +
            + T': $ ) +
            +  F: $ ) * +
        """, dictionary_to_string( follow ) )

    def test_grammarFirstCalculationOfChapter5FollowExample3(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab C D | E F
            A -> aA | &
            C -> E C F | c
            D -> C D | dD d | &
            E -> eE | &
            F -> F S | fF | g
        """ ) )
        first = firstGrammar.first_terminals()

        self.assertTextEqual(
        """
            + S: a b e f g
            + A: & a
            + C: c e
            + D: & c d e
            + E: & e
            + F: f g
        """, dictionary_to_string( first ) )

    def test_grammarFirstNonTerminalCalculationOfChapter5FollowExample3(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab C D | E F
            A -> aA | &
            C -> E C F | c
            D -> C D | dD d | &
            E -> eE | &
            F -> F S | fF | g
        """ ) )
        first_non_terminals = firstGrammar.first_non_terminals()

        self.assertTextEqual(
        """
            + S: A E F
            + A:
            + C: C E
            + D: C E
            + E:
            + F: F
        """, dictionary_to_string( first_non_terminals ) )

    def test_grammarFollowCalculationOfChapter5FollowExample3(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab C D | E F
            A -> aA | &
            C -> E C F | c
            D -> C D | dD d | &
            E -> eE | &
            F -> F S | fF | g
        """ ) )
        follow = firstGrammar.follow_terminals()

        self.assertTextEqual(
        """
            + S: $ a b c d e f g
            + A: b
            + C: $ a b c d e f g
            + D: $ a b c d e f g
            + E: c e f g
            + F: $ a b c d e f g
        """, dictionary_to_string( follow ) )

    def test_grammarFirstCalculationOfChapter5FollowExample4(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A C | C e B | B a
            A -> a A | B C
            B -> b B | A B | &
            C -> c C | &
        """ ) )
        # sys.setrecursionlimit( 2000 )
        first = firstGrammar.first_terminals()

        self.assertTextEqual(
        """
            + S: & a b c e
            + A: & a b c
            + B: & a b c
            + C: & c
        """, dictionary_to_string( first ) )

    def test_grammarFirstNonTerminalCalculationOfChapter5FollowExample4(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A C | C e B | B a
            A -> a A | B C
            B -> b B | A B | &
            C -> c C | &
        """ ) )
        # sys.setrecursionlimit( 2000 )
        first_non_terminals = firstGrammar.first_non_terminals()

        self.assertTextEqual(
        """
            + S: A B C
            + A: A B C
            + B: A B C
            + C:
        """, dictionary_to_string( first_non_terminals ) )

    def test_grammarFollowCalculationOfChapter5FollowExample4(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A C | C e B | B a
            A -> a A | B C
            B -> b B | A B | &
            C -> c C | &
        """ ) )
        # sys.setrecursionlimit( 2000 )
        follow = firstGrammar.follow_terminals()

        self.assertTextEqual(
        """
            + S: $
            + A: $ a b c
            + B: $ a b c
            + C: $ a b c e
        """, dictionary_to_string( follow ) )


if __name__ == "__main__":
    unittest.main()

