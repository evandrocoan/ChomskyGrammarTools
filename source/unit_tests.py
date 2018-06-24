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
        r"""
            cow
        """, dictionary[non_terminal_A] )

    def test_grammarInvalidNonTerminalException(self):

        with self.assertRaisesRegex( RuntimeError, "Invalid Non Terminal `D` added to the grammar" ):
            firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
            r"""
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
        r"""
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
        r"""
            S -> S
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        firstGrammar.remove_production( firstGrammar.initial_symbol, firstGrammar.initial_symbol )

        self.assertTextEqual(
        r"""
            + S' -> S'
            +  A -> & | a A
            +  B -> & | A d | b B
        """, firstGrammar )

    def test_grammarHasRecursionOnNonTerminalChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        non_terminal_S = NonTerminal( "S", lock=True )
        non_terminal_A = NonTerminal( "A", lock=True )

        self.assertFalse( firstGrammar.has_recursion_on_the_non_terminal( non_terminal_S ) )
        self.assertTrue( firstGrammar.has_recursion_on_the_non_terminal( non_terminal_A ) )

    def test_grammarIsEmptyStoSandA(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> B | a
            B -> B
        """ ) )

        self.assertFalse( firstGrammar.is_empty() )

    def test_grammarIsEmptyStoS(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> S
        """ ) )

        self.assertTrue( firstGrammar.is_empty() )

    def test_grammarIsEmptyStoStoBtoB(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> S
            B -> B
        """ ) )

        self.assertTrue( firstGrammar.is_empty() )

    def test_grammarIsEmptyStoSorEpsilon(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> S | &
        """ ) )

        self.assertFalse( firstGrammar.is_empty() )

    def test_grammarIsFiniteStoS(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> B
            B -> B
        """ ) )

        self.assertFalse( firstGrammar.is_finite() )

    def test_grammarIsFiniteStoSorEpsilon(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> S | &
        """ ) )

        self.assertTrue( firstGrammar.is_finite() )

    def test_grammarIsInfiniteStoS(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> B
            B -> B
        """ ) )

        self.assertFalse( firstGrammar.is_infinite() )

    def test_grammarIsInfiniteStoSorEpsilon(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> aS | &
        """ ) )

        self.assertTrue( firstGrammar.is_infinite() )


class TestGrammarFactoringAndRecursionSymbols(TestingUtilities):

    def test_grammarGetNonTerminalSimpleSymbolsChapter4Item5Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> F G H
            F -> G | a
            G -> dG | H | a
            H -> c
        """ ) )
        simple_non_terminals = firstGrammar.simple_non_terminals()

        self.assertTextEqual(
        r"""
            + S: S
            + F: F G H
            + G: G H
            + H: H
        """, dictionary_to_string( simple_non_terminals ) )

    def test_grammarGetNonTerminalSimpleSymbolsChapter4Item5Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> a B c D e
            B -> b B | E | F
            D -> d D | F | d
            E -> e E | e
            F -> f F | f
        """ ) )
        simple_non_terminals = firstGrammar.simple_non_terminals()

        self.assertTextEqual(
        r"""
            + S: S
            + B: B E F
            + D: D F
            + E: E
            + F: F
        """, dictionary_to_string( simple_non_terminals ) )

    def test_grammarEliminateNonTerminalSimpleSymbolsChapter4Item5Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> F G H
            F -> G | a
            G -> dG | H | a
            H -> c
        """ ) )
        firstGrammar.eliminate_simple_non_terminals()

        self.assertTextEqual(
        r"""
            + S -> F G H
            + F -> a | c | d G
            + G -> a | c | d G
            + H -> c
        """, firstGrammar )

    def test_grammarEliminateNonTerminalSimpleSymbolsChapter4Item5Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> a B c D e
            B -> b B | E | F
            D -> d D | F | d
            E -> e E | e
            F -> f F | f
        """ ) )
        firstGrammar.eliminate_simple_non_terminals()

        self.assertTextEqual(
        r"""
            + S -> a B c D e
            + B -> e | f | b B | e E | f F
            + D -> d | f | d D | f F
            + E -> e | e E
            + F -> f | f F
        """, firstGrammar )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item5Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Sa | b
        """ ) )

        self.assertTextEqual(
        r"""
            + (S, 'direct')
        """, convert_to_text_lines( firstGrammar.left_recursion() ) )

    def test_grammarEliminateLeftRecursionCalculationOfChapter5Item5Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Sa | b
        """ ) )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            +  S -> b S'
            + S' -> & | a S'
        """, firstGrammar )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item5Example1Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> aSa | b
        """ ) )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item5Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            E -> E + T | T
            T -> T * F | F
            F -> ( E ) | id
        """ ) )

        self.assertTextEqual(
        r"""
            + (E, 'direct')
            + (T, 'direct')
        """, convert_to_text_lines( firstGrammar.left_recursion() ) )

        self.assertTrue( firstGrammar.has_left_recursion() )

    def test_grammarEliminateLeftRecursionCalculationOfChapter5Item5Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            E -> E + T | T
            F -> ( E ) | id
            T -> T * F | F
        """ ) )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            +  E -> T E'
            +  F -> id | ( E )
            +  T -> id T' | ( E ) T'
            + E' -> & | + T E'
            + T' -> & | * F T'
        """, firstGrammar )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarEliminateLeftRecursionCalculationOfChapter5Item5Example2WithoutSimpleTerminals(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            E -> E + T | T
            T -> T * F | F
            F -> ( E ) | id
        """ ) )
        firstGrammar.eliminate_simple_non_terminals()

        self.assertTextEqual(
        r"""
            + E -> id | ( E ) | E + T | T * F
            + F -> id | ( E )
            + T -> id | ( E ) | T * F
        """, firstGrammar )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            +  E -> id E' | ( E ) E' | T * F E'
            +  F -> id | ( E )
            +  T -> id T' | ( E ) T'
            + E' -> & | + T E'
            + T' -> & | * F T'
        """, firstGrammar )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item5Example2Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            E -> a E + T | T
            T -> b T * T | F
            F -> ( E ) | id
        """ ) )

        self.assertFalse( firstGrammar.has_left_recursion() )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            + E -> T | a E + T
            + F -> id | ( E )
            + T -> F | b T * T
        """, firstGrammar )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item6Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Aa | Sb
            A -> Sc | d
        """ ) )

        self.assertTextEqual(
        r"""
            + (A, 'indirect')
            + (S, 'direct')
        """, convert_to_text_lines( firstGrammar.left_recursion(), sort=sort_correctly ) )

        self.assertTrue( firstGrammar.has_left_recursion() )

    def test_grammarEliminateLeftRecursionOfChapter5Item6Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Aa | Sb
            A -> Sc | d
        """ ) )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            +  S -> A a S'
            +  A -> d A'
            + A' -> & | a S' c A'
            + S' -> & | b S'
        """, firstGrammar )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item6Example1Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> aAa | bSb
            A -> Sc | d
        """ ) )

        self.assertFalse( firstGrammar.has_left_recursion() )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            + S -> a A a | b S b
            + A -> d | S c
        """, firstGrammar )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item6Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> aS | Ab
            A -> Ab | Bc | a
            B -> Bd | Sa | e
        """ ) )

        self.assertTextEqual(
        r"""
            + (A, 'direct')
            + (B, 'direct')
            + (S, 'indirect')
        """, convert_to_text_lines( firstGrammar.left_recursion() ) )

        self.assertTrue( firstGrammar.has_left_recursion() )

    def test_grammarEliminateLeftRecursionCalculationOfChapter5Item6Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> aS | Ab
            A -> Ab | Bc | a
            B -> Bd | Sa | e
        """ ) )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            +  S -> A b | a S
            +  A -> a A' | B c A'
            +  B -> e B' | a S a B' | a A' b a B'
            + A' -> & | b A'
            + B' -> & | d B' | c A' b a B'
        """, firstGrammar )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item6Example2Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> aS | aAb
            A -> aAb | bBc | a
            B -> bBd | aSa | e
        """ ) )

        self.assertFalse( firstGrammar.has_left_recursion() )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            + S -> a S | a A b
            + A -> a | a A b | b B c
            + B -> e | a S a | b B d
        """, firstGrammar )

    def test_grammarEliminateLeftRecursionCalculationOfExercise6List3ItemC(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Bd | &
            A -> Sa | &
            B -> Ab | Bc
        """ ) )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            +  S' -> & | B d
            +   A -> a | S a
            +   B -> b B' | a b B' | S a b B'
            +   S -> b B' d S'' | a b B' d S''
            +  B' -> & | c B'
            + S'' -> & | a b B' d S''
        """, firstGrammar )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarEliminateLeftRecursionOfList3Exercice7ItemA(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            P -> D L | &
            C -> V = exp | id (E)
            D -> d D | &
            E -> exp , E | exp
            L -> L ;C | C
            V -> id [E] | id
        """ ) )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            +  P -> & | L | D L
            +  C -> V = exp | id ( E )
            +  D -> d | d D
            +  E -> exp | exp , E
            +  L -> V = exp L' | id ( E ) L'
            +  V -> id | id [ E ]
            + L' -> & | ; C L'
        """, firstGrammar )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarConvertToProperCalculationOfExercise6List3ItemC(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Bd | &
            A -> Sa | &
            B -> Ab | Bc
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        r"""
            + S' -> & | B d
            +  A -> a | S a
            +  B -> b | A b | B c
            +  S -> B d
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarIsFactoredCalculationOfChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )

        self.assertTextEqual(
        r"""
            + (A, a)
            + (B, a)
            + (B, b)
            + (B, d)
            + (S, a)
            + (S, a)
            + (S, b)
            + (S, b)
            + (S, c)
            + (S, d)
        """, convert_to_text_lines( firstGrammar.factors(), sort=sort_correctly ) )

        self.assertFalse( firstGrammar.is_factored() )

    def test_grammarIsFactoredOfList3Exercice7ItemA(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            P  -> & | L | D L
            C  -> V = exp | id (E)
            D  -> d | d D
            E  -> exp | exp , E
            L  -> V = exp L' | id (E) L'
            V  -> id | id [E]
            L' -> & | ;C L'
        """ ) )

        self.assertTextEqual(
        r"""
            + (C, id)
            + (C, id)
            + (D, d)
            + (D, d)
            + (E, exp)
            + (E, exp)
            + (L, id)
            + (L, id)
            + (P, d)
            + (P, id)
            + (V, id)
            + (V, id)
            + (L', ;)
        """, convert_to_text_lines( firstGrammar.factors(), sort=sort_correctly ) )

    def test_grammarFactoringOfChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        factor_it = firstGrammar.factor_it(3)

        self.assertTextEqual(
        r"""
            +  S -> c | d c | a S1 | b S2
            +  A -> & | a A
            +  B -> & | d | b B | a A d
            + S1 -> c | d c | a S3 | b S4
            + S2 -> & | c | d c | b B c | a A d c
            + S3 -> c | d c | a S5 | b S6
            + S4 -> & | c | d c | b B c | a A d c
            + S5 -> A b | A B c | A d c
            + S6 -> & | B c
        """, firstGrammar )

        self.assertTextEqual(
        r"""
            + (S5, a)
            + (S5, b)
            + (S5, d)
        """, convert_to_text_lines( get_duplicated_elements( firstGrammar.factors() ) ) )

        self.assertFalse( factor_it )
        self.assertFalse( firstGrammar.is_factored() )

    def test_grammarFactoringOfList3Exercice7ItemA(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            P  -> & | L | D L
            C  -> V = exp | id ( E )
            D  -> d | d D
            E  -> exp | exp , E
            L  -> V = exp L' | id (E) L'
            V  -> id | id [E]
            L' -> & | ;C L'
        """ ) )

        factor_it = firstGrammar.factor_it(5)
        self.assertTextEqual(
        r"""
            +  P -> & | d P1 | id P2
            +  C -> id C1
            +  D -> d D1
            +  E -> exp E1
            +  L -> id L1
            +  V -> id V1
            + C1 -> = exp | ( E ) | [ E ] = exp
            + D1 -> & | D
            + E1 -> & | , E
            + L1 -> = exp L' | ( E ) L' | [ E ] = exp L'
            + L' -> & | ; C L'
            + P1 -> L | D L
            + P2 -> = exp L' | ( E ) L' | [ E ] = exp L'
            + V1 -> & | [ E ]
        """, firstGrammar )

        self.assertTrue( factor_it )
        self.assertTrue( firstGrammar.is_factored() )
        self.assertTextEqual( " No elements found.", convert_to_text_lines( get_duplicated_elements( firstGrammar.factors() ) ) )


class TestGrammarFirstAndFollow(TestingUtilities):

    def test_grammarNonTerminalFirstCalculationOfChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        first_non_terminals = firstGrammar.first_non_terminals()

        self.assertTextEqual(
        r"""
            + S: A B
            + A:
            + B: A
        """, dictionary_to_string( first_non_terminals ) )

    def test_grammarFirstCalculationOfChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        first = firstGrammar.first_terminals()

        self.assertTextEqual(
        r"""
            + S: a b c d
            + A: & a
            + B: & a b d
        """, dictionary_to_string( first ) )

    def test_grammarFollowCalculationOfChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        follow = firstGrammar.follow_terminals()

        self.assertTextEqual(
        r"""
            + S: $
            + A: $ a b c d
            + B: c
        """, dictionary_to_string( follow ) )

    def test_grammarFirstNonTermianlCalculationOfChapter5Example1Follow(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> A B C
            A -> aA | &
            B -> bB | A Cd
            C -> cC | &
        """ ) )
        first_non_terminals = firstGrammar.first_non_terminals()

        self.assertTextEqual(
        r"""
            + S: A B C
            + A:
            + B: A C
            + C:
        """, dictionary_to_string( first_non_terminals ) )

    def test_grammarFirstCalculationOfChapter5Example1Follow(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> A B C
            A -> aA | &
            B -> bB | A Cd
            C -> cC | &
        """ ) )
        first = firstGrammar.first_terminals()

        self.assertTextEqual(
        r"""
            + S: a b c d
            + A: & a
            + B: a b c d
            + C: & c
        """, dictionary_to_string( first ) )

    def test_grammarFollowCalculationOfChapter5Example1Follow(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> A B C
            A -> aA | &
            B -> bB | A Cd
            C -> cC | &
        """ ) )
        follow = firstGrammar.follow_terminals()

        self.assertTextEqual(
        r"""
            + S: $
            + A: $ a b c d
            + B: $ c
            + C: $ d
        """, dictionary_to_string( follow ) )

    def test_grammarFirstCalculationOfChapter5FollowExample2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            E  -> T E'
            E' -> + T E' | &
            T  -> F T'
            T' -> * F T' | &
            F  -> ( E ) | id | i
        """ ) )
        first = firstGrammar.first_terminals()

        self.assertTextEqual(
        r"""
            +  E: ( i id
            + E': & +
            +  T: ( i id
            + T': & *
            +  F: ( i id
        """, dictionary_to_string( first ) )

    def test_grammarFirstNonTerminalCalculationOfChapter5FollowExample2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            E  -> T E'
            E' -> + T E' | &
            T  -> F T'
            T' -> * F T' | &
            F  -> ( E ) | id
        """ ) )
        first_non_terminals = firstGrammar.first_non_terminals()

        self.assertTextEqual(
        r"""
            +  E: F T
            + E':
            +  T: F
            + T':
            +  F:
        """, dictionary_to_string( first_non_terminals ) )

    def test_grammarFollowCalculationOfChapter5FollowExample2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            E  -> T E'
            E' -> + T E' | &
            T  -> F T'
            T' -> * F T' | &
            F  -> ( E ) | id
        """ ) )
        follow = firstGrammar.follow_terminals()

        self.assertTextEqual(
        r"""
            +  E: $ )
            + E': $ )
            +  T: $ ) +
            + T': $ ) +
            +  F: $ ) * +
        """, dictionary_to_string( follow ) )

    def test_grammarFirstCalculationOfChapter5FollowExample3(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab C D | E F
            A -> aA | &
            C -> E C F | c
            D -> C D | dD d | &
            E -> eE | &
            F -> F S | fF | g
        """ ) )
        first = firstGrammar.first_terminals()

        self.assertTextEqual(
        r"""
            + S: a b e f g
            + A: & a
            + C: c e
            + D: & c d e
            + E: & e
            + F: f g
        """, dictionary_to_string( first ) )

    def test_grammarFirstNonTerminalCalculationOfChapter5FollowExample3(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab C D | E F
            A -> aA | &
            C -> E C F | c
            D -> C D | dD d | &
            E -> eE | &
            F -> F S | fF | g
        """ ) )
        first_non_terminals = firstGrammar.first_non_terminals()

        self.assertTextEqual(
        r"""
            + S: A E F
            + A:
            + C: C E
            + D: C E
            + E:
            + F: F
        """, dictionary_to_string( first_non_terminals ) )

    def test_grammarFollowCalculationOfChapter5FollowExample3(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab C D | E F
            A -> aA | &
            C -> E C F | c
            D -> C D | dD d | &
            E -> eE | &
            F -> F S | fF | g
        """ ) )
        follow = firstGrammar.follow_terminals()

        self.assertTextEqual(
        r"""
            + S: $ a b c d e f g
            + A: b
            + C: $ a b c d e f g
            + D: $ a b c d e f g
            + E: c e f g
            + F: $ a b c d e f g
        """, dictionary_to_string( follow ) )

    def test_grammarFirstCalculationOfChapter5FollowExample4(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> A C | C e B | B a
            A -> a A | B C
            B -> b B | A B | &
            C -> c C | &
        """ ) )
        # sys.setrecursionlimit( 2000 )
        first = firstGrammar.first_terminals()

        self.assertTextEqual(
        r"""
            + S: & a b c e
            + A: & a b c
            + B: & a b c
            + C: & c
        """, dictionary_to_string( first ) )

    def test_grammarFirstNonTerminalCalculationOfChapter5FollowExample4(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> A C | C e B | B a
            A -> a A | B C
            B -> b B | A B | &
            C -> c C | &
        """ ) )
        # sys.setrecursionlimit( 2000 )
        first_non_terminals = firstGrammar.first_non_terminals()

        self.assertTextEqual(
        r"""
            + S: A B C
            + A: A B C
            + B: A B C
            + C:
        """, dictionary_to_string( first_non_terminals ) )

    def test_grammarFollowCalculationOfChapter5FollowExample4(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> A C | C e B | B a
            A -> a A | B C
            B -> b B | A B | &
            C -> c C | &
        """ ) )
        # sys.setrecursionlimit( 2000 )
        follow = firstGrammar.follow_terminals()

        self.assertTextEqual(
        r"""
            + S: $
            + A: $ a b c
            + B: $ a b c
            + C: $ a b c e
        """, dictionary_to_string( follow ) )


class TestAutomataOperationHistory(TestingUtilities):
    """
        Tests automata operations history creation.
    """

    def test_historySuccessfulFactoringHistory(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            P  -> & | L | D L
            C  -> V = exp | id (E)
            D  -> d | d D
            E  -> exp | exp , E
            L  -> V = exp L' | id (E) L'
            V  -> id | id [E]
            L' -> & | ;C L'
        """ ) )
        firstGrammar.factor_it(5)

        self.assertTextEqual(
        r"""
            + # 1. Factoring, Beginning
            +   P -> & | L | D L
            +   C -> V = exp | id ( E )
            +   D -> d | d D
            +   E -> exp | exp , E
            +   L -> V = exp L' | id ( E ) L'
            +   V -> id | id [ E ]
            +  L' -> & | ; C L'
            +
            + # 2. Eliminating Indirect Factors, End
            + # Indirect factors for elimination: [(L, L), (D L, D), (V = exp, V), (V = exp L', V), (V = exp L', V)]
            +   P -> & | d L | d D L | id ( E ) L' | id = exp L' | id [ E ] = exp L'
            +   C -> id ( E ) | id = exp | id [ E ] = exp
            +   D -> d | d D
            +   E -> exp | exp , E
            +   L -> id ( E ) L' | id = exp L' | id [ E ] = exp L'
            +   V -> id | id [ E ]
            +  L' -> & | ; C L'
            +
            + # 3. Eliminating Direct Factors, End
            + # Direct factors for elimination: [(C, id), (D, d), (E, exp), (L, id), (P, d), (P, id), (V, id)]
            +   P -> & | d P1 | id P2
            +   C -> id C1
            +   D -> d D1
            +   E -> exp E1
            +   L -> id L1
            +   V -> id V1
            +  C1 -> = exp | ( E ) | [ E ] = exp
            +  D1 -> & | D
            +  E1 -> & | , E
            +  L1 -> = exp L' | ( E ) L' | [ E ] = exp L'
            +  L' -> & | ; C L'
            +  P1 -> L | D L
            +  P2 -> = exp L' | ( E ) L' | [ E ] = exp L'
            +  V1 -> & | [ E ]
        """, firstGrammar.get_operation_history() )

    def test_historyFactoringOfList3Exercice7ItemA(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            P  -> & | L | D L
            C  -> V = exp | id ( E )
            D  -> d | d D
            E  -> exp | exp , E
            L  -> V = exp L' | id (E) L'
            V  -> id | id [E] | i
            L' -> & | ;C L'
        """ ) )

        factor_it = firstGrammar.factor_it(5)
        self.assertTextEqual(
        r"""
            + # 1. Factoring, Beginning
            +   P -> & | L | D L
            +   C -> V = exp | id ( E )
            +   D -> d | d D
            +   E -> exp | exp , E
            +   L -> V = exp L' | id ( E ) L'
            +   V -> i | id | id [ E ]
            +  L' -> & | ; C L'
            +
            + # 2. Eliminating Indirect Factors, End
            + # Indirect factors for elimination: [(L, L), (D L, D), (V = exp, V), (V = exp L', V), (V = exp L', V)]
            +   P -> & | d L | d D L | i = exp L' | id ( E ) L' | id = exp L' | id [ E ] = exp L'
            +   C -> i = exp | id ( E ) | id = exp | id [ E ] = exp
            +   D -> d | d D
            +   E -> exp | exp , E
            +   L -> i = exp L' | id ( E ) L' | id = exp L' | id [ E ] = exp L'
            +   V -> i | id | id [ E ]
            +  L' -> & | ; C L'
            +
            + # 3. Eliminating Direct Factors, End
            + # Direct factors for elimination: [(C, id), (D, d), (E, exp), (L, id), (P, d), (P, id), (V, id)]
            +   P -> & | d P1 | id P2 | i = exp L'
            +   C -> id C1 | i = exp
            +   D -> d D1
            +   E -> exp E1
            +   L -> id L1 | i = exp L'
            +   V -> i | id V1
            +  C1 -> = exp | ( E ) | [ E ] = exp
            +  D1 -> & | D
            +  E1 -> & | , E
            +  L1 -> = exp L' | ( E ) L' | [ E ] = exp L'
            +  L' -> & | ; C L'
            +  P1 -> L | D L
            +  P2 -> = exp L' | ( E ) L' | [ E ] = exp L'
            +  V1 -> & | [ E ]
        """, firstGrammar.get_operation_history() )

    def test_historyEliminateLeftRecursionCalculationOfChapter5Item5Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            E -> E + T | T
            F -> ( E ) | id
            T -> T * F | F
        """ ) )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            + # 1. Eliminating Left Recursion, Beginning
            +  E -> T | E + T
            +  F -> id | ( E )
            +  T -> F | T * F
            +
            + # 2. Eliminating Infertile Symbols, End
            +  E -> T | E + T
            +  F -> id | ( E )
            +  T -> F | T * F
            +
            + # 3. Eliminating Unreachable Symbols, End
            +  E -> T | E + T
            +  F -> id | ( E )
            +  T -> F | T * F
            +
            + # 4. Eliminate direct left recursion
            +   E -> T E'
            +   F -> id | ( E )
            +   T -> F | T * F
            +  E' -> & | + T E'
            +
            + # 5. Eliminate indirect left recursion
            +   E -> T E'
            +   F -> id | ( E )
            +   T -> id | ( E ) | T * F
            +  E' -> & | + T E'
            +
            + # 6. Eliminate direct left recursion
            +   E -> T E'
            +   F -> id | ( E )
            +   T -> id T' | ( E ) T'
            +  E' -> & | + T E'
            +  T' -> & | * F T'
        """, firstGrammar.get_operation_history() )


class TestGrammarEpsilonConversion(TestingUtilities):

    def test_grammarConvertToEpsilonFreeChapter4Item4Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> A B
            A -> aA | &
            B -> bB | &
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        r"""
            + S -> & | A | B | A B
            + A -> a | a A
            + B -> b | b B
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarConvertToEpsilonFreeChapter4Item4Example1Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> A B | S S
            A -> aA | &
            B -> bB | &
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        r"""
            + S' -> & | A | B | A B | S S
            +  A -> a | a A
            +  B -> b | b B
            +  S -> A | B | A B | S S
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarConvertToEpsilonFreeChapter4Item4Example2Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> c S c | B a
            A -> aA | A B C | &
            B -> bB | C A | &
            C -> c C c | A S
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        r"""
            + S -> a | B a | c S c
            + A -> a | C | a A | A C | B C | A B C
            + B -> b | C | b B | C A
            + C -> S | A S | c C c
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarConvertToEpsilonFreeChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        r"""
            + S -> b | c | A b | A c | B c | A B c
            + A -> a | a A
            + B -> b | d | A d | b B
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarConvertToEpsilonFreeWithNewInitialSymbolChapter5Example1FirstMutatedWithEpsilonS(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab | A Bc | A B S | &
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        r"""
            + S' -> & | b | c | A | B | S | A b | A c | B c | A B | A S | B S | A B c | A B S
            +  A -> a | a A
            +  B -> b | d | A d | b B
            +  S -> b | c | A | B | S | A b | A c | B c | A B | A S | B S | A B c | A B S
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarConvertToEpsilonFreeWithNewInitialSymbolChapter5Example1FirstMutatedS(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab | A Bc | A B S
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        r"""
            + S -> b | c | S | A b | A c | B c | A S | B S | A B c | A B S
            + A -> a | a A
            + B -> b | d | A d | b B
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarConvertToEpsilonFreeWithNewInitialSymbolChapter5Example1FirstMutatedNoS(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab | A Bc | A B
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        r"""
            + S -> & | b | c | A | B | A b | A c | B c | A B | A B c
            + A -> a | a A
            + B -> b | d | A d | b B
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarGetNonTerminalEpsilonSimpleCaseChapter5Example1First(self):
        LockableType._USE_STRING = False
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
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
        """, wrap_text( sort_alphabetically_and_by_length( firstGrammar.non_terminal_epsilon() ), wrap=100 ) )

    def test_grammarGetNonTerminalEpsilonChapter5Example1FirstMutated(self):
        LockableType._USE_STRING = False
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
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
        """, wrap_text( sort_alphabetically_and_by_length( firstGrammar.non_terminal_epsilon() ), wrap=100 ) )

    def test_grammarIsNotEpsilonFreeChapter5Example1First(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )

        self.assertFalse( firstGrammar.is_epsilon_free() )

    def test_grammarIsEpsilonFreeChapter5Example1FirstEpsilonFreed(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
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
        r"""
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
        r"""
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
        r"""
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
        r"""
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
        r"""
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
        r"""
            S -> aS | B C | B D
            A -> cC | A B
            B -> bB | &
            C -> aA | B C
            D -> d D d | c
        """ ) )
        firstGrammar.eliminate_infertile()

        self.assertTextEqual(
        r"""
            + S -> a S | B D
            + B -> & | b B
            + D -> c | d D d
        """, firstGrammar )

    def test_grammarEliminateUnreachableSymbolsChapter4Item1Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> aS | B C | B D
            A -> cC | A B
            B -> bB | &
            C -> aA | B C
            D -> d D d | c
        """ ) )
        firstGrammar.eliminate_unreachable()

        self.assertTextEqual(
        r"""
            + S -> a S | B C | B D
            + A -> c C | A B
            + B -> & | b B
            + C -> a A | B C
            + D -> c | d D d
        """, firstGrammar )

    def test_grammarGetReachableChapter4Item1Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> aSa | dDd
            A -> aB | Cc | a
            B -> dD | bB | b
            C -> Aa | dD | c
            D -> bbB | d
        """ ) )
        reachable = firstGrammar.reachable()

        self.assertTextEqual(
        r"""
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
        r"""
            S -> aSa | dDd
            A -> aB | Cc | a
            B -> dD | bB | b
            C -> Aa | dD | c
            D -> bbB | d
        """ ) )
        firstGrammar.eliminate_unreachable()

        self.assertTextEqual(
        r"""
            + S -> a S a | d D d
            + B -> b | b B | d D
            + D -> d | bb B
        """, firstGrammar )

    def test_grammarEliminateUnusefulSymbolsChapter4Item1Example3(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
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
        r"""
            + S -> S a | b F d
            + A -> & | a A
            + C -> & | c a
            + F -> A b | a C | b F d
        """, firstGrammar )

    def test_grammarGetNonTerminalSimpleSymbolsChapter4Item3Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> a F G | b F d | S a
            A -> a A | &
            B -> c G | a C G
            C -> c B a | c a | &
            D -> d C c | &
            F -> b F d | a C | A b | G A
            G -> B c | B C a
        """ ) )
        non_terminal_epsilon = firstGrammar.non_terminal_epsilon()
        simple_non_terminals = firstGrammar.simple_non_terminals()

        self.assertTextEqual(
        r"""
            + Production locked: True, str: A, symbols: [NonTerminal locked: True, str: A, sequence: 1, len: 1;], sequence: 1, len: 1;
            + Production locked: True, str: C, symbols: [NonTerminal locked: True, str: C, sequence: 1, len: 1;], sequence: 1, len: 1;
            + Production locked: True, str: D, symbols: [NonTerminal locked: True, str: D, sequence: 1, len: 1;], sequence: 1, len: 1;
        """, wrap_text( convert_to_text_lines( non_terminal_epsilon, new_line=False ), wrap=120 ) )

        self.assertTextEqual(
        r"""
            + S -> S a | a F G | b F d
            + A -> a | a A
            + B -> a G | c G | a C G
            + C -> c a | c B a
            + D -> d c | d C c
            + F -> a | b | G | A b | a C | G A | b F d
            + G -> B a | B c | B C a
        """, firstGrammar )

        self.assertTextEqual(
        r"""
            + S: S
            + A: A
            + B: B
            + C: C
            + D: D
            + F: F G
            + G: G
        """, wrap_text( convert_to_text_lines( simple_non_terminals, new_line=False ), wrap=120 ) )


class TestGrammarTreeParsing(TestingUtilities):

    def test_grammarTreeParsingComplexSingleProduction(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        r"""
            S -> aABbbCC1aAbA BC | ba | c
        """ ) )

        self.assertTextEqual(
        r"""
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
        r"""
            S  -> aABbbCC1aAbA BC | ba | c
            A  -> &
            AB -> &
            BC -> &
            CC -> &
        """ )

        self.assertTextEqual(
        r"""
            +  S -> c | ba | a AB bb CC 1a A b A BC
            +  A -> &
            + AB -> &
            + BC -> &
            + CC -> &
        """, firstGrammar )

    def test_grammarInputParsingSymbolMerging(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines(
        r"""
            S -> a b cd | AccD | Ac cD
            A -> &
            D -> &
        """ )

        self.assertTextEqual(
        r"""
            + S -> a b cd | A cc D | A c c D
            + A -> &
            + D -> &
        """, str( firstGrammar ) )

    def test_grammarTreeParsingABandB(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        r"""
            S -> aABb BC | b
        """ ) )

        self.assertTextEqual(
        r"""
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
        r"""
             S ->
            SS -> S |
        """ )

        self.assertTextEqual(
        r"""
            +  S -> &
            + SS -> & | S
        """, str( firstGrammar ) )

    def test_grammarTreeParsingEmptyEpsilon(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        r"""
             S ->
            SS -> S |
        """ ) )

        self.assertTextEqual(
        r"""
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
        r"""
            S   -> SS SSS | &
            SS  -> &
            SSS -> &
        """ )

        self.assertTextEqual(
        r"""
            +   S -> & | SS SSS
            +  SS -> &
            + SSS -> &
        """, str( firstGrammar ) )

    def test_grammarTreeParsingSSandEpsilon(self):
        firstGrammar = ChomskyGrammar.parse(
        r"""
            S -> S SS | &
        """ )

        self.assertTextEqual(
        r"""
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
        r"""
            S -> S S | &
        """ ) )

        self.assertTextEqual(
        r"""
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

    def test_grammarSpecialSymbolsList3Exercice7ItemA(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        r"""
            P -> D L | &
            C -> V=exp | id (E)
            D -> d D | &
            E -> exp , E | exp
            L -> L ;C | C
            V -> id[E] | id
        """ ) )

        self.assertTextEqual(
        r"""
            + productions
            +   non_terminal_start
            +     non_terminal  P
            +   space
            +   non_terminals
            +     production
            +       space
            +       non_terminal  D
            +       space
            +       non_terminal  L
            +       space
            +     production
            +       space
            +       epsilon
            +   end_symbol
            +     new_line
            +
            +   non_terminal_start
            +     non_terminal  C
            +   space
            +   non_terminals
            +     production
            +       space
            +       non_terminal  V
            +       terminal
            +         equals
            +         e
            +         x
            +         p
            +       space
            +     production
            +       space
            +       terminal
            +         i
            +         d
            +       space
            +       terminal
            +         open_paren
            +       non_terminal  E
            +       terminal
            +         close_paren
            +   end_symbol
            +     new_line
            +
            +   non_terminal_start
            +     non_terminal  D
            +   space
            +   non_terminals
            +     production
            +       space
            +       terminal  d
            +       space
            +       non_terminal  D
            +       space
            +     production
            +       space
            +       epsilon
            +   end_symbol
            +     new_line
            +
            +   non_terminal_start
            +     non_terminal  E
            +   space
            +   non_terminals
            +     production
            +       space
            +       terminal
            +         e
            +         x
            +         p
            +       space
            +       terminal
            +         comma
            +       space
            +       non_terminal  E
            +       space
            +     production
            +       space
            +       terminal
            +         e
            +         x
            +         p
            +   end_symbol
            +     new_line
            +
            +   non_terminal_start
            +     non_terminal  L
            +   space
            +   non_terminals
            +     production
            +       space
            +       non_terminal  L
            +       space
            +       terminal
            +         semicolon
            +       non_terminal  C
            +       space
            +     production
            +       space
            +       non_terminal  C
            +   end_symbol
            +     new_line
            +
            +   non_terminal_start
            +     non_terminal  V
            +   space
            +   non_terminals
            +     production
            +       space
            +       terminal
            +         i
            +         d
            +         open_bracket
            +       non_terminal  E
            +       terminal
            +         close_bracket
            +       space
            +     production
            +       space
            +       terminal
            +         i
            +         d
        """, firstGrammar.pretty() )


class TestGrammarTreeTransformation(TestingUtilities):

    def setUp(self):
        super().setUp()
        LockableType._USE_STRING = False

    def test_grammarTransformationTreeParsingParenStarPlusSymbols(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        r"""
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
        r"""
            S -> aABbbCC1aAbA BC | ba | c
        """ ) )
        firstGrammar = ChomskyGrammarTreeTransformer().transform( firstGrammar )

        self.assertTextEqual(
        r"""
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
            + [Production locked: True, str: a a, symbols: [Terminal locked: True, str: a, sequence: 1, len: 1;,
            + Terminal locked: True, str: a, sequence: 2, len: 1;], sequence: 2, len: 2;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationFilterNonTerminalsFromaAa(self):
        symbols = [self.ta, self.ntA, self.ta.new()]
        production = Production( symbols )
        production.filter_non_terminals( symbols, [] )

        self.assertTextEqual(
        r"""
            + [Terminal locked: True, str: a, sequence: 1, len: 1;, Terminal locked: True, str: a, sequence: 2, len: 1;]
        """, sort_alphabetically_and_by_length( production ) )

    def test_combinationFilterNonTerminalsFromAa(self):
        symbols = [self.ntA, self.ta]
        production = Production( symbols )
        production.filter_non_terminals( symbols, [] )

        self.assertTextEqual(
        r"""
            + [Terminal locked: True, str: a, sequence: 1, len: 1;]
        """, sort_alphabetically_and_by_length( production ) )


if __name__ == "__main__":
    unittest.main()

