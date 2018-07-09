#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# Licensing
#
# Unit Tests
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
import sys
import lark

import unittest
import profile
import cProfile

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
from grammar.dynamic_iteration import DynamicIterationDict

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
            self.fail( "Recent created Epsilon Production did evaluate to `True`" )

    def test_grammarEpsilonProductionEvalutesNotTrueOnIf(self):

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


class TestGrammarLeftRecursionEliminationSymbols(TestingUtilities):

    def test_getDirectAndIndirectLeftRecursion(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            P -> P a | &
            M -> P M | M a
        """ ) )

        self.assertTextEqual(
        r"""
            + (M, 'direct')
            + (P, 'direct')
            + (M, 'indirect')
        """, convert_to_text_lines( firstGrammar.left_recursion() ) )

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
            + # 1. Eliminating Simple Productions, Beginning
            +  S -> F G H
            +  F -> a | G
            +  G -> a | H | d G
            +  H -> c
            +
            + # 2. Converting to Epsilon Free, End
            + #    No changes performed.
            +
            + # 3. Eliminating Simple Productions, End
            + #    Simple Non Terminals: S -> {S}; F -> {F, G, H}; G -> {G, H}; H -> {H}
            +  S -> F G H
            +  F -> a | c | d G
            +  G -> a | c | d G
            +  H -> c
        """, firstGrammar.get_operation_history() )

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
            + # 1. Eliminating Simple Productions, Beginning
            +  S -> a B c D e
            +  B -> E | F | b B
            +  D -> d | F | d D
            +  E -> e | e E
            +  F -> f | f F
            +
            + # 2. Converting to Epsilon Free, End
            + #    No changes performed.
            +
            + # 3. Eliminating Simple Productions, End
            + #    Simple Non Terminals: S -> {S}; B -> {B, E, F}; D -> {D, F}; E -> {E}; F -> {F}
            +  S -> a B c D e
            +  B -> e | f | b B | e E | f F
            +  D -> d | f | d D | f F
            +  E -> e | e E
            +  F -> f | f F
        """, firstGrammar.get_operation_history() )

    def test_grammarEliminateNonTerminalSimpleSymbolsChapter4Item5Example2NoSimple(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> a B c D e
            B -> b B
            D -> d D | d
            E -> e E | e
            F -> f F | f
        """ ) )
        firstGrammar.eliminate_simple_non_terminals()

        self.assertTextEqual(
        r"""
            + # 1. Eliminating Simple Productions, Beginning
            +  S -> a B c D e
            +  B -> b B
            +  D -> d | d D
            +  E -> e | e E
            +  F -> f | f F
            +
            + # 2. Converting to Epsilon Free, End
            + #    No changes performed.
        """, firstGrammar.get_operation_history() )

    def test_grammarEliminateLeftRecursionCalculationOfChapter5Item5Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Sa | b
        """ ) )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            + # 1. Eliminating Left Recursion, Beginning
            +  S -> b | S a
            +
            + # 2. Eliminating Infertile Symbols, End
            + #    No changes performed.
            +
            + # 3. Eliminating Unreachable Symbols, End
            + #    No changes performed.
            +
            + # 4. Eliminating Left Recursion, End
            + #    Direct recursion eliminated: {S a} -> {b S'} @ S' -> {a S', &}
            +   S -> b S'
            +  S' -> & | a S'
        """, firstGrammar.get_operation_history() )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item5Example1Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> aSa | b
        """ ) )

        self.assertFalse( firstGrammar.has_left_recursion() )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            + # 1. Eliminating Left Recursion, Beginning
            + #    No changes performed.
            +  S -> b | a S a
        """, firstGrammar.get_operation_history() )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_historyEliminateLeftRecursionCalculationOfChapter5Item5Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            E -> E + T | T
            F -> ( E ) | id
            T -> T * F | F
        """ ) )

        self.assertTrue( firstGrammar.has_left_recursion() )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            + # 1. Eliminating Left Recursion, Beginning
            +  E -> T | E + T
            +  F -> id | ( E )
            +  T -> F | T * F
            +
            + # 2. Eliminating Infertile Symbols, End
            + #    No changes performed.
            +
            + # 3. Eliminating Unreachable Symbols, End
            + #    No changes performed.
            +
            + # 4. Eliminating Left Recursion, End
            + #    Direct recursion eliminated: {E + T} -> {T E'} @ E' -> {+ T E', &}
            + #    Direct recursion eliminated: {T * F} -> {F T'} @ T' -> {* F T', &}
            +   E -> T E'
            +   F -> id | ( E )
            +   T -> F T'
            +  E' -> & | + T E'
            +  T' -> & | * F T'
        """, firstGrammar.get_operation_history() )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarHasLeftRecursionCalculationOfChapter5Item5Example2Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            E -> a E + T | T
            F -> ( E ) | id
            T -> b T * T | F
        """ ) )

        self.assertFalse( firstGrammar.has_left_recursion() )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            + # 1. Eliminating Left Recursion, Beginning
            + #    No changes performed.
            +  E -> T | a E + T
            +  F -> id | ( E )
            +  T -> F | b T * T
        """, firstGrammar.get_operation_history() )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarEliminateLeftRecursionOfChapter5Item6Example1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Aa | Sb
            A -> Sc | d
        """ ) )

        self.assertTrue( firstGrammar.has_left_recursion() )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            + # 1. Eliminating Left Recursion, Beginning
            +  S -> A a | S b
            +  A -> d | S c
            +
            + # 2. Eliminating Infertile Symbols, End
            + #    No changes performed.
            +
            + # 3. Eliminating Unreachable Symbols, End
            + #    Direct recursion eliminated: {S b} -> {A a S'} @ S' -> {b S', &}
            +  S -> A a | S b
            +  A -> d | S c
            +
            + # 4. Eliminate indirect left recursion
            + #    Indirect recursion eliminated: {A: {(A a S' >> S c => A a S' c)}}
            +   S -> A a S'
            +   A -> d | A a S' c
            +  S' -> & | b S'
            +
            + # 5. Eliminate direct left recursion
            + #    Direct recursion eliminated: {A a S' c} -> {d A'} @ A' -> {a S' c A', &}
            +   S -> A a S'
            +   A -> d A'
            +  A' -> & | a S' c A'
            +  S' -> & | b S'
        """, firstGrammar.get_operation_history() )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarEliminateLeftRecursionOfChapter5Item6Example1Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Aa | Sb | &
            A -> Sc | d | C D
            C -> C
            D -> d
        """ ) )

        self.assertTrue( firstGrammar.has_left_recursion() )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            + # 1. Eliminating Left Recursion, Beginning
            +  S -> & | A a | S b
            +  A -> d | S c | C D
            +  C -> C
            +  D -> d
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: S -> &
            +  S' -> & | b | A a | S b
            +   A -> c | d | S c | C D
            +   C -> C
            +   D -> d
            +   S -> b | A a | S b
            +
            + # 3. Eliminating Infertile Symbols, End
            + #    Infertile symbols: {A -> C D, C -> C}
            +  S' -> & | b | A a | S b
            +   A -> c | d | S c
            +   D -> d
            +   S -> b | A a | S b
            +
            + # 4. Eliminating Unreachable Symbols, End
            + #    Unreachable symbols: {D -> {d}}
            +  S' -> & | b | A a | S b
            +   A -> c | d | S c
            +   S -> b | A a | S b
            +
            + # 5. Eliminate indirect left recursion
            + #    Indirect recursion eliminated: {S: {(S c >> A a => S c a), (d >> A a => d a), (c >> A a => c a)}}
            +  S' -> & | b | A a | S b
            +   A -> c | d | S c
            +   S -> b | c a | d a | S b | S c a
            +
            + # 6. Eliminate direct left recursion
            + #    Direct recursion eliminated: {S b, S c a} -> {b S'', d a S'', c a S''} @ S'' -> {b S'', c a S'', &}
            +   S' -> & | b | A a | S b
            +    A -> c | d | S c
            +    S -> b S'' | c a S'' | d a S''
            +  S'' -> & | b S'' | c a S''
        """, firstGrammar.get_operation_history() )

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
            + # 1. Eliminating Left Recursion, Beginning
            + #    No changes performed.
            +  S -> a A a | b S b
            +  A -> d | S c
        """, firstGrammar.get_operation_history() )

        self.assertFalse( firstGrammar.has_left_recursion() )

    def test_grammarEliminateLeftRecursionCalculationOfChapter5Item6Example2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> aS | Ab
            A -> Ab | Bc | a
            B -> Bd | Sa | e
        """ ) )

        self.assertTrue( firstGrammar.has_left_recursion() )
        firstGrammar.eliminate_left_recursion()

        self.assertTextEqual(
        r"""
            + # 1. Eliminating Left Recursion, Beginning
            +  S -> A b | a S
            +  A -> a | A b | B c
            +  B -> e | B d | S a
            +
            + # 2. Eliminating Infertile Symbols, End
            + #    No changes performed.
            +
            + # 3. Eliminating Unreachable Symbols, End
            + #    Direct recursion eliminated: {A b} -> {B c A', a A'} @ A' -> {b A', &}
            +  S -> A b | a S
            +  A -> a | A b | B c
            +  B -> e | B d | S a
            +
            + # 4. Eliminate indirect left recursion
            + #    Indirect recursion eliminated: {B: {(B c A' >> A b a => B c A' b a), (a A' >> A b a => a A' b a)}}
            +   S -> A b | a S
            +   A -> a A' | B c A'
            +   B -> e | B d | a S a | a A' b a | B c A' b a
            +  A' -> & | b A'
            +
            + # 5. Eliminate direct left recursion
            + #    Direct recursion eliminated: {B d, B c A' b a} -> {e B', a S a B', a A' b a B'} @ B' -> {d B', c A' b a B', &}
            +   S -> A b | a S
            +   A -> a A' | B c A'
            +   B -> e B' | a S a B' | a A' b a B'
            +  A' -> & | b A'
            +  B' -> & | d B' | c A' b a B'
        """, firstGrammar.get_operation_history() )

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
            + # 1. Eliminating Left Recursion, Beginning
            + #    No changes performed.
            +  S -> a S | a A b
            +  A -> a | a A b | b B c
            +  B -> e | a S a | b B d
        """, firstGrammar.get_operation_history() )

        self.assertFalse( firstGrammar.has_left_recursion() )

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
            + # 1. Eliminating Left Recursion, Beginning
            +  S -> & | B d
            +  A -> & | S a
            +  B -> A b | B c
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: S -> &; A -> &
            +  S' -> & | B d
            +   A -> a | S a
            +   B -> b | A b | B c
            +   S -> B d
            +
            + # 3. Eliminating Infertile Symbols, End
            + #    No changes performed.
            +
            + # 4. Eliminating Unreachable Symbols, End
            + #    No changes performed.
            +
            + # 5. Eliminate indirect left recursion
            + #    Indirect recursion eliminated: {B: {(S a >> A b => S a b), (a >> A b => a b)}}
            +  S' -> & | B d
            +   A -> a | S a
            +   B -> b | a b | B c | S a b
            +   S -> B d
            +
            + # 6. Eliminate direct left recursion
            + #    Direct recursion eliminated: {B c} -> {b B', S a b B', a b B'} @ B' -> {c B', &}
            +  S' -> & | B d
            +   A -> a | S a
            +   B -> b B' | a b B' | S a b B'
            +   S -> B d
            +  B' -> & | c B'
            +
            + # 7. Eliminate indirect left recursion
            + #    Indirect recursion eliminated: {S: {(b B' >> B d => b B' d), (S a b B' >> B d => S a b B' d), (a b B' >> B d => a b B' d)}}
            +  S' -> & | B d
            +   A -> a | S a
            +   B -> b B' | a b B' | S a b B'
            +   S -> b B' d | a b B' d | S a b B' d
            +  B' -> & | c B'
            +
            + # 8. Eliminate direct left recursion
            + #    Direct recursion eliminated: {S a b B' d} -> {b B' d S'', a b B' d S''} @ S'' -> {a b B' d S'', &}
            +   S' -> & | B d
            +    A -> a | S a
            +    B -> b B' | a b B' | S a b B'
            +    S -> b B' d S'' | a b B' d S''
            +   B' -> & | c B'
            +  S'' -> & | a b B' d S''
        """, firstGrammar.get_operation_history() )

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
            + # 1. Eliminating Left Recursion, Beginning
            +  P -> & | D L
            +  C -> V = exp | id ( E )
            +  D -> & | d D
            +  E -> exp | exp , E
            +  L -> C | L ; C
            +  V -> id | id [ E ]
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: P -> &; D -> &
            +  P -> & | L | D L
            +  C -> V = exp | id ( E )
            +  D -> d | d D
            +  E -> exp | exp , E
            +  L -> C | L ; C
            +  V -> id | id [ E ]
            +
            + # 3. Eliminating Infertile Symbols, End
            + #    No changes performed.
            +
            + # 4. Eliminating Unreachable Symbols, End
            + #    No changes performed.
            +
            + # 5. Eliminating Left Recursion, End
            + #    Direct recursion eliminated: {L ; C} -> {C L'} @ L' -> {; C L', &}
            +   P -> & | L | D L
            +   C -> V = exp | id ( E )
            +   D -> d | d D
            +   E -> exp | exp , E
            +   L -> C L'
            +   V -> id | id [ E ]
            +  L' -> & | ; C L'
        """, firstGrammar.get_operation_history() )

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
            + # 1. Converting to Epsilon Free, Beginning
            +  S -> & | B d
            +  A -> & | S a
            +  B -> A b | B c
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: S -> &; A -> &
            +  S' -> & | B d
            +   A -> a | S a
            +   B -> b | A b | B c
            +   S -> B d
        """, firstGrammar.get_operation_history() )

        self.assertTrue( firstGrammar.is_epsilon_free() )


class TestGrammarFactoringElimination(TestingUtilities):

    def test_grammarFactorsOfChapter5Example1First(self):
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
            + (B, A)
            + (S, A)
            + (S, A)
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
            + # 1. Factoring, Beginning
            +  S -> A b | A B c
            +  A -> & | a A
            +  B -> & | A d | b B
            +
            + # 2. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {S: [A]}
            +   S -> A S1
            +   A -> & | a A
            +   B -> & | A d | b B
            +  S1 -> b | B c
            +
            + # 3. Eliminating Indirect Factors, End
            + #    Indirect factors eliminated: {S1: B c => b B c | A d c | c}
            +   S -> A S1
            +   A -> & | a A
            +   B -> & | A d | b B
            +  S1 -> b | c | A d c | b B c
            +
            + # 4. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {S1: [b]}
            +   S -> A S1
            +   A -> & | a A
            +   B -> & | A d | b B
            +  S1 -> c | b S2 | A d c
            +  S2 -> & | B c
        """, firstGrammar.get_operation_history() )

        self.assertTextEqual(
        r"""
            + No elements found.
        """, convert_to_text_lines( get_duplicated_elements( firstGrammar.factors() ) ) )

        self.assertTrue( factor_it )
        self.assertEqual( 4, firstGrammar.last_factoring_step )
        self.assertTrue( firstGrammar.is_factored() )

    def test_grammarFactorsOfList3Exercice7ItemA(self):
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
            + (C, V)
            + (L', ;)
            + (L, V)
            + (P, D)
            + (P, L)
        """, convert_to_text_lines( firstGrammar.factors(), sort=sort_correctly ) )

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
        factor_it = firstGrammar.factor_it(10)

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
            + # 2. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {D: [d], E: [exp], V: [id]}
            +   P -> & | L | D L
            +   C -> V = exp | id ( E )
            +   D -> d D1
            +   E -> exp E1
            +   L -> V = exp L' | id ( E ) L'
            +   V -> id V1
            +  D1 -> & | D
            +  E1 -> & | , E
            +  L' -> & | ; C L'
            +  V1 -> & | [ E ]
            +
            + # 3. Eliminating Indirect Factors, End
            + #    Indirect factors eliminated: {C: V = exp => id V1 = exp, L: V = exp L' => id V1 = exp L'}
            +   P -> & | L | D L
            +   C -> id ( E ) | id V1 = exp
            +   D -> d D1
            +   E -> exp E1
            +   L -> id ( E ) L' | id V1 = exp L'
            +   V -> id V1
            +  D1 -> & | D
            +  E1 -> & | , E
            +  L' -> & | ; C L'
            +  V1 -> & | [ E ]
            +
            + # 4. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {C: [id], L: [id]}
            +   P -> & | L | D L
            +   C -> id C1
            +   D -> d D1
            +   E -> exp E1
            +   L -> id L1
            +   V -> id V1
            +  C1 -> ( E ) | V1 = exp
            +  D1 -> & | D
            +  E1 -> & | , E
            +  L1 -> ( E ) L' | V1 = exp L'
            +  L' -> & | ; C L'
            +  V1 -> & | [ E ]
        """, firstGrammar.get_operation_history() )

        self.assertTrue( factor_it )
        self.assertTrue( firstGrammar.is_factored() )
        self.assertEqual( 4, firstGrammar.last_factoring_step )
        self.assertTextEqual(
        r"""
            + No elements found.
        """, convert_to_text_lines( get_duplicated_elements( firstGrammar.factors() ) ) )

    def test_historyFactorsOfList3Exercice7ItemAMutated(self):
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

        self.assertTextEqual(
        r"""
            + (C, i)
            + (C, id)
            + (C, id)
            + (D, d)
            + (D, d)
            + (E, exp)
            + (E, exp)
            + (L, i)
            + (L, id)
            + (L, id)
            + (P, d)
            + (P, i)
            + (P, id)
            + (V, i)
            + (V, id)
            + (V, id)
            + (C, V)
            + (L', ;)
            + (L, V)
            + (P, D)
            + (P, L)
        """, convert_to_text_lines( firstGrammar.factors(), sort=sort_correctly ) )

    def test_historyFactoringOfList3Exercice7ItemAMutated(self):
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
            + # 2. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {D: [d], E: [exp], V: [id]}
            +   P -> & | L | D L
            +   C -> V = exp | id ( E )
            +   D -> d D1
            +   E -> exp E1
            +   L -> V = exp L' | id ( E ) L'
            +   V -> i | id V1
            +  D1 -> & | D
            +  E1 -> & | , E
            +  L' -> & | ; C L'
            +  V1 -> & | [ E ]
            +
            + # 3. Eliminating Indirect Factors, End
            + #    Indirect factors eliminated: {C: V = exp => i = exp | id V1 = exp, L: V = exp L' => i = exp L' | id V1 = exp L'}
            +   P -> & | L | D L
            +   C -> i = exp | id ( E ) | id V1 = exp
            +   D -> d D1
            +   E -> exp E1
            +   L -> i = exp L' | id ( E ) L' | id V1 = exp L'
            +   V -> i | id V1
            +  D1 -> & | D
            +  E1 -> & | , E
            +  L' -> & | ; C L'
            +  V1 -> & | [ E ]
            +
            + # 4. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {C: [id], L: [id]}
            +   P -> & | L | D L
            +   C -> id C1 | i = exp
            +   D -> d D1
            +   E -> exp E1
            +   L -> id L1 | i = exp L'
            +   V -> i | id V1
            +  C1 -> ( E ) | V1 = exp
            +  D1 -> & | D
            +  E1 -> & | , E
            +  L1 -> ( E ) L' | V1 = exp L'
            +  L' -> & | ; C L'
            +  V1 -> & | [ E ]
        """, firstGrammar.get_operation_history() )

        self.assertTrue( factor_it )
        self.assertTrue( firstGrammar.is_factored() )
        self.assertEqual( 4, firstGrammar.last_factoring_step )
        self.assertTextEqual(
        r"""
            + No elements found.
        """, convert_to_text_lines( get_duplicated_elements( firstGrammar.factors() ) ) )

    def test_historyFactorsOfSimpleNonTerminalsFactors(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> M | M m
            M -> m | &
        """ ) )

        self.assertTextEqual(
        r"""
            + (M, m)
            + (S, m)
            + (S, m)
            + (S, M)
            + (S, M)
        """, convert_to_text_lines( firstGrammar.factors(), sort=sort_correctly ) )

    def test_historyFactoringOfSimpleNonTerminalsFactors(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> M | M m
            M -> m | &
        """ ) )

        factor_it = firstGrammar.factor_it(2)
        self.assertTextEqual(
        r"""
            + # 1. Factoring, Beginning
            +  S -> M | M m
            +  M -> & | m
            +
            + # 2. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {S: [M]}
            +   S -> M S1
            +   M -> & | m
            +  S1 -> & | m
        """, firstGrammar.get_operation_history() )

    def test_historyFactoringOfComplexNonTerminalsFactors(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            P -> d P | M L
            M -> m ; M | &
            L -> C ; L a | &
            C -> id ( E ) | id = E | b P e | C # id | &
            E -> E + id | id
        """ ) )

        factor_it = firstGrammar.factor_it(5)
        self.assertTextEqual(
        r"""
            + # 1. Factoring, Beginning
            +  P -> d P | M L
            +  C -> & | b P e | C # id | id = E | id ( E )
            +  E -> id | E + id
            +  L -> & | C ; L a
            +  M -> & | m ; M
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: M -> &; L -> &; C -> &; P -> &
            +  P' -> & | d | L | M | d P | M L
            +   C -> b e | # id | b P e | C # id | id = E | id ( E )
            +   E -> id | E + id
            +   L -> ; a | ; L a | C ; a | C ; L a
            +   M -> m ; | m ; M
            +   P -> d | L | M | d P | M L
            +
            + # 3. Eliminating Infertile Symbols, End
            + #    No changes performed.
            +
            + # 4. Eliminating Unreachable Symbols, End
            + #    No changes performed.
            +
            + # 5. Eliminating Left Recursion, End
            + #    Direct recursion eliminated: {C # id} -> {id ( E ) C', id = E C', b P e C', b e C', # id C'} @ C' -> {# id C', &}
            + #    Direct recursion eliminated: {E + id} -> {id E'} @ E' -> {+ id E', &}
            +  P' -> & | d | L | M | d P | M L
            +   C -> b e C' | # id C' | b P e C' | id = E C' | id ( E ) C'
            +   E -> id E'
            +   L -> ; a | ; L a | C ; a | C ; L a
            +   M -> m ; | m ; M
            +   P -> d | L | M | d P | M L
            +  C' -> & | # id C'
            +  E' -> & | + id E'
            +
            + # 6. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {P: [M, d], M: [m ;], L: [;, C ;], C: [b, id], P': [M, d]}
            +   P' -> & | L | d P'2 | M P'1
            +    C -> b C1 | id C2 | # id C'
            +    E -> id E'
            +    L -> ; L1 | C ; L2
            +    M -> m ; M1
            +    P -> L | d P2 | M P1
            +   C1 -> e C' | P e C'
            +   C2 -> = E C' | ( E ) C'
            +   C' -> & | # id C'
            +   E' -> & | + id E'
            +   L1 -> a | L a
            +   L2 -> a | L a
            +   M1 -> & | M
            +   P1 -> & | L
            +   P2 -> & | P
            +  P'1 -> & | L
            +  P'2 -> & | P
        """, firstGrammar.get_operation_history() )

        self.assertTrue( factor_it )
        self.assertTrue( firstGrammar.is_factored() )
        self.assertEqual( 2, firstGrammar.last_factoring_step )
        self.assertTextEqual(
        r"""
            + No elements found.
        """, convert_to_text_lines( get_duplicated_elements( firstGrammar.factors() ) ) )

    def test_historyFactorsByTerminalsAbndAbAndAbInOneProduction(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> a b d | a b b d  | A b a b d | B b a b d | c
            A -> a
            B -> a
        """ ) )

        self.assertTextEqual(
        r"""
            + (A, a)
            + (B, a)
            + (S, a b)
            + (S, a b)
            + (S, a)
            + (S, a)
            + (S, c)
            + (S, A)
            + (S, B)
        """, convert_to_text_lines( firstGrammar.factors(), sort=sort_correctly ) )

    def test_historyFactorsByTerminalsAaAndAaInOneProduction(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> a a d | a a b d  | a a a b d | c
        """ ) )

        self.assertTextEqual(
        r"""
            + (S, a a)
            + (S, a a)
            + (S, a a)
            + (S, c)
        """, convert_to_text_lines( firstGrammar.factors(), sort=sort_correctly ) )

    def test_historyFactorsByTerminalsAaAndAaaInOneProduction(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> a d | a a b d  | a a a b d | c
        """ ) )

        self.assertTextEqual(
        r"""
            + (S, a)
            + (S, a)
            + (S, a)
            + (S, c)
        """, convert_to_text_lines( firstGrammar.factors(), sort=sort_correctly ) )

    def test_historyFactorsByNonTerminalsAandAAandAAAInOneProduction(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> A S | A A B S  | A A A B S | c
            A -> a
            B -> b
        """ ) )

        self.assertTextEqual(
        r"""
            + (A, a)
            + (B, b)
            + (S, a)
            + (S, a)
            + (S, a)
            + (S, c)
            + (S, A)
            + (S, A)
            + (S, A)
        """, convert_to_text_lines( firstGrammar.factors(), sort=sort_correctly ) )

    def test_historyFactorsByNonTerminalsAAandAAAInOneProduction(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> A A S | A A A B S | c
            A -> a
            B -> b
        """ ) )

        self.assertTextEqual(
        r"""
            + (A, a)
            + (B, b)
            + (S, a)
            + (S, a)
            + (S, c)
            + (S, A A)
            + (S, A A)
        """, convert_to_text_lines( firstGrammar.factors(), sort=sort_correctly ) )

    def test_historyFactorsByNonTerminalsAAandAAInOneProduction(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> A A S | A A B S | c
            A -> a
            B -> b
        """ ) )

        self.assertTextEqual(
        r"""
            + (A, a)
            + (B, b)
            + (S, a)
            + (S, a)
            + (S, c)
            + (S, A A)
            + (S, A A)
        """, convert_to_text_lines( firstGrammar.factors(), sort=sort_correctly ) )

    def test_historyFactoringByTerminalsInOneProduction(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> a a a | a a S | a a B S | a a C S | d
            B -> b
            C -> c
        """ ) )

        factor_it = firstGrammar.factor_it(5)
        self.assertTextEqual(
        r"""
            + # 1. Factoring, Beginning
            +  S -> d | a a a | a a S | a a B S | a a C S
            +  B -> b
            +  C -> c
            +
            + # 2. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {S: [a a]}
            +   S -> d | a a S1
            +   B -> b
            +   C -> c
            +  S1 -> a | S | B S | C S
            +
            + # 3. Eliminating Indirect Factors, End
            + #    Indirect factors eliminated: {S1: S => d | a a S1, S1: B S => b S, S1: C S => c S}
            +   S -> d | a a S1
            +   B -> b
            +   C -> c
            +  S1 -> a | d | b S | c S | a a S1
            +
            + # 4. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {S1: [a]}
            +   S -> d | a a S1
            +   B -> b
            +   C -> c
            +  S1 -> d | b S | c S | a S2
            +  S2 -> & | a S1
        """, firstGrammar.get_operation_history() )

        self.assertTrue( factor_it )
        self.assertTrue( firstGrammar.is_factored() )
        self.assertEqual( 4, firstGrammar.last_factoring_step )
        self.assertTextEqual(
        r"""
            + No elements found.
        """, convert_to_text_lines( get_duplicated_elements( firstGrammar.factors() ) ) )

    def test_historyFactoringByTerminalsAndNonTerminalsIndirectly(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> a | A a
            A -> a
        """ ) )

        factor_it = firstGrammar.factor_it(5)
        self.assertTextEqual(
        r"""
            + # 1. Factoring, Beginning
            +  S -> a | A a
            +  A -> a
            +
            + # 2. Eliminating Indirect Factors, End
            + #    Indirect factors eliminated: {S: A a => a a}
            +  S -> a | a a
            +  A -> a
            +
            + # 3. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {S: [a]}
            +   S -> a S1
            +   A -> a
            +  S1 -> & | a
        """, firstGrammar.get_operation_history() )

        self.assertTrue( factor_it )
        self.assertTrue( firstGrammar.is_factored() )
        self.assertEqual( 3, firstGrammar.last_factoring_step )
        self.assertTextEqual(
        r"""
            + No elements found.
        """, convert_to_text_lines( get_duplicated_elements( firstGrammar.factors() ) ) )

    def test_historyFactoringByTerminalsMixedInOneProduction(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> a a a | a a a S | a a B S | a a C S | d
            A -> a
            B -> b
            C -> c
        """ ) )

        factor_it = firstGrammar.factor_it(5)
        self.assertTextEqual(
        r"""
            + # 1. Factoring, Beginning
            +  S -> d | a a a | a a a S | a a B S | a a C S
            +  A -> a
            +  B -> b
            +  C -> c
            +
            + # 2. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {S: [a a]}
            +   S -> d | a a S1
            +   A -> a
            +   B -> b
            +   C -> c
            +  S1 -> a | a S | B S | C S
            +
            + # 3. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {S1: [a]}
            +   S -> d | a a S1
            +   A -> a
            +   B -> b
            +   C -> c
            +  S1 -> B S | C S | a S2
            +  S2 -> & | S
        """, firstGrammar.get_operation_history() )

        self.assertTrue( factor_it )
        self.assertTrue( firstGrammar.is_factored() )
        self.assertEqual( 3, firstGrammar.last_factoring_step )
        self.assertTextEqual(
        r"""
            + No elements found.
        """, convert_to_text_lines( get_duplicated_elements( firstGrammar.factors() ) ) )

    def test_historyFactoringByNonTerminalsInOneProduction(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> A A A | A A S | A A B S | A A C S | d
            A -> a
            B -> b
            C -> c
        """ ) )

        factor_it = firstGrammar.factor_it(5)
        self.assertTextEqual(
        r"""
            + # 1. Factoring, Beginning
            +  S -> d | A A A | A A S | A A B S | A A C S
            +  A -> a
            +  B -> b
            +  C -> c
            +
            + # 2. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {S: [A A]}
            +   S -> d | A A S1
            +   A -> a
            +   B -> b
            +   C -> c
            +  S1 -> A | S | B S | C S
            +
            + # 3. Eliminating Indirect Factors, End
            + #    Indirect factors eliminated: {S1: A => a, S1: S => d | A A S1, S1: B S => b S, S1: C S => c S}
            +   S -> d | A A S1
            +   A -> a
            +   B -> b
            +   C -> c
            +  S1 -> a | d | b S | c S | A A S1
            +
            + # 4. Eliminating Indirect Factors, End
            + #    Indirect factors eliminated: {S1: A A S1 => a A S1}
            +   S -> d | A A S1
            +   A -> a
            +   B -> b
            +   C -> c
            +  S1 -> a | d | b S | c S | a A S1
            +
            + # 5. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {S1: [a]}
            +   S -> d | A A S1
            +   A -> a
            +   B -> b
            +   C -> c
            +  S1 -> d | b S | c S | a S2
            +  S2 -> & | A S1
        """, firstGrammar.get_operation_history() )

        self.assertTrue( factor_it )
        self.assertTrue( firstGrammar.is_factored() )
        self.assertEqual( 5, firstGrammar.last_factoring_step )
        self.assertTextEqual(
        r"""
            + No elements found.
        """, convert_to_text_lines( get_duplicated_elements( firstGrammar.factors() ) ) )

    # @unittest.skip( "In construction" )
    def test_historyFactoringByNonTerminalsMixedInOneProduction(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> a A A | A A S | A A B S | A A C S | d
            A -> a
            B -> b
            C -> c
        """ ) )

        factor_it = firstGrammar.factor_it(10)
        self.assertTextEqual(
        r"""
            + # 1. Factoring, Beginning
            +  S -> d | a A A | A A S | A A B S | A A C S
            +  A -> a
            +  B -> b
            +  C -> c
            +
            + # 2. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {S: [A A]}
            +   S -> d | a A A | A A S1
            +   A -> a
            +   B -> b
            +   C -> c
            +  S1 -> S | B S | C S
            +
            + # 3. Eliminating Indirect Factors, End
            + #    Indirect factors eliminated: {S: A A S1 => a A S1}
            +   S -> d | a A A | a A S1
            +   A -> a
            +   B -> b
            +   C -> c
            +  S1 -> S | B S | C S
            +
            + # 4. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {S: [a A]}
            +   S -> d | a A S2
            +   A -> a
            +   B -> b
            +   C -> c
            +  S1 -> S | B S | C S
            +  S2 -> A | S1
            +
            + # 5. Eliminating Indirect Factors, End
            + #    Indirect factors eliminated: {S2: A => a, S2: S1 => S | B S | C S}
            +   S -> d | a A S2
            +   A -> a
            +   B -> b
            +   C -> c
            +  S1 -> S | B S | C S
            +  S2 -> a | S | B S | C S
            +
            + # 6. Eliminating Indirect Factors, End
            + #    Indirect factors eliminated: {S2: S => a A S2 | d, S2: B S => b S, S2: C S => c S}
            +   S -> d | a A S2
            +   A -> a
            +   B -> b
            +   C -> c
            +  S1 -> S | B S | C S
            +  S2 -> a | d | b S | c S | a A S2
            +
            + # 7. Eliminating Direct Factors, End
            + #    Direct factors eliminated: {S2: [a]}
            +   S -> d | a A S2
            +   A -> a
            +   B -> b
            +   C -> c
            +  S1 -> S | B S | C S
            +  S2 -> d | b S | c S | a S3
            +  S3 -> & | A S2
        """, firstGrammar.get_operation_history() )

        self.assertTrue( factor_it )
        self.assertTrue( firstGrammar.is_factored() )
        self.assertEqual( 7, firstGrammar.last_factoring_step )
        self.assertTextEqual(
        r"""
            + No elements found.
        """, convert_to_text_lines( get_duplicated_elements( firstGrammar.factors() ) ) )


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

    def test_grammarFirstCalculationOfChapter5Example1FirstMutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab | A B
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        first = firstGrammar.first_terminals()

        self.assertTextEqual(
        r"""
            + S: & a b d
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
            + A: a b c d
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
            + A: a b c d
            + B: $ c
            + C: $ d
        """, dictionary_to_string( follow ) )

    def test_grammarFollowCalculationOfExerciseList4Item6(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            C -> com C'
            C' -> ; V := exp C' | &
            V -> id V'
            V' -> [ exp ] | &
        """ ) )
        follow = firstGrammar.follow_terminals()

        self.assertTextEqual(
        r"""
            +  C: $
            + C': $
            +  V: :=
            + V': :=
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


class TestGrammarEpsilonConversion(TestingUtilities):

    def test_grammarConvertToEpsilonFreeWithTerminalOnTheMiddle(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> & | a A
            A -> b | S b S
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        r"""
            + # 1. Converting to Epsilon Free, Beginning
            +  S -> & | a A
            +  A -> b | S b S
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: S -> &
            +  S' -> & | a A
            +   A -> b | b S | S b | S b S
            +   S -> a A
        """, firstGrammar.get_operation_history() )

        self.assertTrue( firstGrammar.is_epsilon_free() )

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
            + # 1. Converting to Epsilon Free, Beginning
            +  S -> A B
            +  A -> & | a A
            +  B -> & | b B
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: A -> &; B -> &; S -> &
            +  S -> & | A | B | A B
            +  A -> a | a A
            +  B -> b | b B
        """, firstGrammar.get_operation_history() )

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
            + # 1. Converting to Epsilon Free, Beginning
            +  S -> A B | S S
            +  A -> & | a A
            +  B -> & | b B
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: A -> &; B -> &; S -> &
            +  S' -> & | A | B | S | A B | S S
            +   A -> a | a A
            +   B -> b | b B
            +   S -> A | B | S | A B | S S
        """, firstGrammar.get_operation_history() )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarConvertToEpsilonFreeChapter4Item4Example1EmptyLanguage(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> A B S | S S
            A -> aA | &
            B -> bB | &
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        r"""
            + # 1. Converting to Epsilon Free, Beginning
            +  S -> S S | A B S
            +  A -> & | a A
            +  B -> & | b B
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: A -> &; B -> &
            +  S -> S | A S | B S | S S | A B S
            +  A -> a | a A
            +  B -> b | b B
        """, firstGrammar.get_operation_history() )

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
            + # 1. Converting to Epsilon Free, Beginning
            +  S -> B a | c S c
            +  A -> & | a A | A B C
            +  B -> & | b B | C A
            +  C -> A S | c C c
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: A -> &; B -> &
            +  S -> a | B a | c S c
            +  A -> a | C | a A | A C | B C | A B C
            +  B -> b | C | b B | C A
            +  C -> S | A S | c C c
        """, firstGrammar.get_operation_history() )

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
            + # 1. Converting to Epsilon Free, Beginning
            +  S -> A b | A B c
            +  A -> & | a A
            +  B -> & | A d | b B
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: A -> &; B -> &
            +  S -> b | c | A b | A c | B c | A B c
            +  A -> a | a A
            +  B -> b | d | A d | b B
        """, firstGrammar.get_operation_history() )

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
            + # 1. Converting to Epsilon Free, Beginning
            +  S -> & | A b | A B c | A B S
            +  A -> & | a A
            +  B -> & | A d | b B
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: S -> &; A -> &; B -> &
            +  S' -> & | b | c | A | B | S | A b | A c | B c | A B | A S | B S | A B c | A B S
            +   A -> a | a A
            +   B -> b | d | A d | b B
            +   S -> b | c | A | B | S | A b | A c | B c | A B | A S | B S | A B c | A B S
        """, firstGrammar.get_operation_history() )

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
            + # 1. Converting to Epsilon Free, Beginning
            +  S -> A b | A B c | A B S
            +  A -> & | a A
            +  B -> & | A d | b B
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: A -> &; B -> &
            +  S -> b | c | S | A b | A c | B c | A S | B S | A B c | A B S
            +  A -> a | a A
            +  B -> b | d | A d | b B
        """, firstGrammar.get_operation_history() )

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
            + # 1. Converting to Epsilon Free, Beginning
            +  S -> A b | A B | A B c
            +  A -> & | a A
            +  B -> & | A d | b B
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: A -> &; B -> &; S -> &
            +  S -> & | b | c | A | B | A b | A c | B c | A B | A B c
            +  A -> a | a A
            +  B -> b | d | A d | b B
        """, firstGrammar.get_operation_history() )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarIsEpsilonFreeChapter5Example1FirstEpsilonFreed(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab | A Bc | &
            A -> aA | a
            B -> bB | Ad
        """ ) )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarGetNonTerminalEpsilonSimpleCaseChapter5Example1First(self):
        LockableType._USE_STRING = False
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        self.assertFalse( firstGrammar.is_epsilon_free() )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: A, len: 1, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;], sequence: 1;
            + , Production locked: True, str: B, len: 1, symbols: [NonTerminal locked: True, str: B, len: 1,
            + sequence: 1;], sequence: 1;
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
            + [Production locked: True, str: A, len: 1, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;], sequence: 1;
            + , Production locked: True, str: B, len: 1, symbols: [NonTerminal locked: True, str: B, len: 1,
            + sequence: 1;], sequence: 1;
            + , Production locked: True, str: S, len: 1, symbols: [NonTerminal locked: True, str: S, len: 1,
            + sequence: 1;], sequence: 1;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( firstGrammar.non_terminal_epsilon() ), wrap=100 ) )


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
            + [Production locked: True, str: A, len: 1, symbols: [NonTerminal locked: True, str: A, len: 1, sequence: 1;], sequence: 1;
            + , Production locked: True, str: B, len: 1, symbols: [NonTerminal locked: True, str: B, len: 1, sequence: 1;], sequence: 1;
            + , Production locked: True, str: C, len: 1, symbols: [NonTerminal locked: True, str: C, len: 1, sequence: 1;], sequence: 1;
            + , Production locked: True, str: S, len: 1, symbols: [NonTerminal locked: True, str: S, len: 1, sequence: 1;], sequence: 1;
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
            + [Production locked: True, str: B, len: 1, symbols: [NonTerminal locked: True, str: B, len: 1, sequence: 1;], sequence: 1;
            + , Production locked: True, str: C, len: 1, symbols: [NonTerminal locked: True, str: C, len: 1, sequence: 1;], sequence: 1;
            + , Production locked: True, str: S, len: 1, symbols: [NonTerminal locked: True, str: S, len: 1, sequence: 1;], sequence: 1;
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
            + [Production locked: True, str: E, len: 1, symbols: [NonTerminal locked: True, str: E, len: 1, sequence: 1;], sequence: 1;
            + , Production locked: True, str: F, len: 1, symbols: [NonTerminal locked: True, str: F, len: 1, sequence: 1;], sequence: 1;
            + , Production locked: True, str: T, len: 1, symbols: [NonTerminal locked: True, str: T, len: 1, sequence: 1;], sequence: 1;
            + , Production locked: True, str: E', len: 1, symbols: [NonTerminal locked: True, str: E', len: 1, sequence: 1;], sequence: 1;
            + , Production locked: True, str: T', len: 1, symbols: [NonTerminal locked: True, str: T', len: 1, sequence: 1;], sequence: 1;
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
            + [Production locked: True, str: E', len: 1, symbols: [NonTerminal locked: True, str: E', len: 1, sequence: 1;], sequence: 1;
            + , Production locked: True, str: T', len: 1, symbols: [NonTerminal locked: True, str: T', len: 1, sequence: 1;], sequence: 1;
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
            + [Production locked: True, str: B, len: 1, symbols: [NonTerminal locked: True, str: B, len: 1, sequence: 1;], sequence: 1;
            + , Production locked: True, str: D, len: 1, symbols: [NonTerminal locked: True, str: D, len: 1, sequence: 1;], sequence: 1;
            + , Production locked: True, str: S, len: 1, symbols: [NonTerminal locked: True, str: S, len: 1, sequence: 1;], sequence: 1;
            + ]
        """, sort_alphabetically_and_by_length( fertile ) )

    def test_grammarEliminateInfertileNonTerminalsChapter4Item1Example1(self):
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
            + # 1. Eliminating Infertile Symbols, Beginning
            +  S -> a S | B C | B D
            +  A -> c C | A B
            +  B -> & | b B
            +  C -> a A | B C
            +  D -> c | d D d
            +
            + # 2. Eliminating Infertile Symbols, End
            + #    Infertile symbols: {S -> B C, A -> c C, A -> A B, C -> a A, C -> B C}
            +  S -> a S | B D
            +  B -> & | b B
            +  D -> c | d D d
        """, firstGrammar.get_operation_history() )

    def test_grammarEliminateUnreachableSymbolsChapter4Item1Example1Mutated(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> aS | B C | B D
            A -> cC | A B
            B -> bB | &
            C -> aA | B C
            D -> dD d | c
            H -> aC
        """ ) )
        firstGrammar.eliminate_unreachable()

        self.assertTextEqual(
        r"""
            + # 1. Eliminating Unreachable Symbols, Beginning
            +  S -> a S | B C | B D
            +  A -> c C | A B
            +  B -> & | b B
            +  C -> a A | B C
            +  D -> c | d D d
            +  H -> a C
            +
            + # 2. Eliminating Unreachable Symbols, End
            + #    Unreachable symbols: {H -> {a C}}
            +  S -> a S | B C | B D
            +  A -> c C | A B
            +  B -> & | b B
            +  C -> a A | B C
            +  D -> c | d D d
        """, firstGrammar.get_operation_history() )

    def test_grammarGetReachableChapter4Item1Example2WithyEpsilon(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        r"""
            S -> aSa | dDd | &
            A -> aB | Cc | a
            B -> dD | bB | b
            C -> Aa | dD | c
            D -> bbB | d
        """ ) )
        reachable = firstGrammar.reachable()

        self.assertTextEqual(
        r"""
            + Terminal locked: True, str: &, len: 0, sequence: 1;
            + Terminal locked: True, str: a, len: 1, sequence: 1;
            + Terminal locked: True, str: b, len: 1, sequence: 1;
            + Terminal locked: True, str: bb, len: 1, sequence: 1;
            + Terminal locked: True, str: d, len: 1, sequence: 1;
            + NonTerminal locked: True, str: B, len: 1, sequence: 2;
            + NonTerminal locked: True, str: D, len: 1, sequence: 2;
            + NonTerminal locked: True, str: S, len: 1, sequence: 1;
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
            + # 1. Eliminating Unreachable Symbols, Beginning
            +  S -> a S a | d D d
            +  A -> a | a B | C c
            +  B -> b | b B | d D
            +  C -> c | A a | d D
            +  D -> d | bb B
            +
            + # 2. Eliminating Unreachable Symbols, End
            + #    Unreachable symbols: {A -> {a B, C c, a}, C -> {d D, c}}
            +  S -> a S a | d D d
            +  B -> b | b B | d D
            +  D -> d | bb B
        """, firstGrammar.get_operation_history() )

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
            + # 1. Eliminating Unuseful Symbols, Beginning
            +  S -> S a | a F G | b F d
            +  A -> & | a A
            +  B -> c G | a C G
            +  C -> & | c a | c B a
            +  D -> & | d C c
            +  F -> A b | a C | G A | b F d
            +  G -> B c | B C a
            +
            + # 2. Eliminating Infertile Symbols, End
            + #    Infertile symbols: {S -> a F G, B -> c G, B -> a C G, C -> c B a, F -> G A, G -> B c, G -> B C a}
            +  S -> S a | b F d
            +  A -> & | a A
            +  C -> & | c a
            +  D -> & | d C c
            +  F -> A b | a C | b F d
            +
            + # 3. Eliminating Unreachable Symbols, End
            + #    Unreachable symbols: {D -> {d C c, &}}
            +  S -> S a | b F d
            +  A -> & | a A
            +  C -> & | c a
            +  F -> A b | a C | b F d
        """, firstGrammar.get_operation_history() )

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
            + Production locked: True, str: A, len: 1, symbols: [NonTerminal locked: True, str: A, len: 1, sequence: 1;], sequence: 1;
            + Production locked: True, str: C, len: 1, symbols: [NonTerminal locked: True, str: C, len: 1, sequence: 1;], sequence: 1;
            + Production locked: True, str: D, len: 1, symbols: [NonTerminal locked: True, str: D, len: 1, sequence: 1;], sequence: 1;
        """, wrap_text( convert_to_text_lines( non_terminal_epsilon, new_line=False ), wrap=120 ) )

        self.assertTextEqual(
        r"""
            + # 1. Converting to Epsilon Free, Beginning
            +  S -> S a | a F G | b F d
            +  A -> & | a A
            +  B -> c G | a C G
            +  C -> & | c a | c B a
            +  D -> & | d C c
            +  F -> A b | a C | G A | b F d
            +  G -> B c | B C a
            +
            + # 2. Converting to Epsilon Free, End
            + #    Non Terminal's Deriving Epsilon: A -> &; C -> &; D -> &
            +  S -> S a | a F G | b F d
            +  A -> a | a A
            +  B -> a G | c G | a C G
            +  C -> c a | c B a
            +  D -> d c | d C c
            +  F -> a | b | G | A b | a C | G A | b F d
            +  G -> B a | B c | B C a
        """, firstGrammar.get_operation_history() )

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

    def test_grammarInputParsingComplexSingleProduction(self):
        grammar = \
        r"""
            S -> aABbbCC1aAbA BC | ba | c
            A -> &
            AB -> &
            BC -> &
            CC1 -> &
        """
        firstGrammar = ChomskyGrammar.load_from_text_lines( grammar )

        self.assertTextEqual(
        r"""
            +   S -> c | ba | a AB bb CC1 a A b A BC
            +   A -> &
            +  AB -> &
            +  BC -> &
            + CC1 -> &
        """, firstGrammar )

    def test_grammarTreeParsingComplexSingleProduction(self):
        grammar = \
        r"""
            S -> aABbbCC1aAbA BC | ba | c
            A -> &
            AB -> &
            BC -> &
            CC1 -> &
        """
        firstGrammar = ChomskyGrammar.parse( grammar )
        new_tree = ChomskyGrammarTreeTransformer().transform( firstGrammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   S
            +   productions
            +     a AB bb CC1 a A b A BC
            +     ba
            +     c
            +   new_line
            +
            +   A
            +   productions  &
            +   new_line
            +
            +   AB
            +   productions  &
            +   new_line
            +
            +   BC
            +   productions  &
            +   new_line
            +
            +   CC1
            +   productions  &
        """, new_tree.pretty() )

    def test_grammarRawTreeParsingComplexSingleProduction(self):
        grammar = \
        r"""
            S -> aABbbCC1aAbA BC | ba | c
            A -> &
            AB -> &
            BC -> &
            CC1 -> &
        """
        firstGrammar = ChomskyGrammar.parse( grammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   start_symbol
            +     production
            +       token
            +         non_terminals  S
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  a
            +       token
            +         non_terminals
            +           A
            +           B
            +       token
            +         terminals
            +           b
            +           b
            +       token
            +         non_terminals
            +           C
            +           C
            +           1
            +       token
            +         terminals  a
            +       token
            +         non_terminals  A
            +       token
            +         terminals  b
            +       token
            +         non_terminals  A
            +
            +       token
            +         non_terminals
            +           B
            +           C
            +
            +     production
            +
            +       token
            +         terminals
            +           b
            +           a
            +
            +     production
            +
            +       token
            +         terminals  c
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals  A
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  &
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals
            +           A
            +           B
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  &
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals
            +           B
            +           C
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  &
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals
            +           C
            +           C
            +           1
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  &
        """, firstGrammar.pretty() )

    def test_grammarInputParsingSymbolMerging(self):
        grammar = \
        r"""
            S -> a b cd | AccD | Ac cD
            A -> &
            D -> &
        """
        firstGrammar = ChomskyGrammar.parse( grammar )
        firstGrammar = ChomskyGrammar.load_from_text_lines( grammar )

        self.assertTextEqual(
        r"""
            + S -> a b cd | A cc D | A c c D
            + A -> &
            + D -> &
        """, firstGrammar )

    def test_grammarTreeParsingSymbolMerging(self):
        grammar = \
        r"""
            S -> a b cd | AccD | Ac cD
            A -> &
            D -> &
        """
        firstGrammar = ChomskyGrammar.parse( grammar )
        new_tree = ChomskyGrammarTreeTransformer().transform( firstGrammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   S
            +   productions
            +     a b cd
            +     A cc D
            +     A c c D
            +   new_line
            +
            +   A
            +   productions  &
            +   new_line
            +
            +   D
            +   productions  &
        """, new_tree.pretty() )

    def test_grammarRawTreeParsingSymbolMerging(self):
        grammar = \
        r"""
            S -> a b cd | AccD | Ac cD
            A -> &
            D -> &
        """
        firstGrammar = ChomskyGrammar.parse( grammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   start_symbol
            +     production
            +       token
            +         non_terminals  S
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  a
            +
            +       token
            +         terminals  b
            +
            +       token
            +         terminals
            +           c
            +           d
            +
            +     production
            +
            +       token
            +         non_terminals  A
            +       token
            +         terminals
            +           c
            +           c
            +       token
            +         non_terminals  D
            +
            +     production
            +
            +       token
            +         non_terminals  A
            +       token
            +         terminals  c
            +
            +       token
            +         terminals  c
            +       token
            +         non_terminals  D
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals  A
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  &
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals  D
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  &
        """, firstGrammar.pretty() )

    def test_grammarInputParsingABandB(self):
        grammar = \
        r"""
            S -> aABb BC | b
            AB -> &
            BC -> &
        """
        firstGrammar = ChomskyGrammar.load_from_text_lines( grammar )

        self.assertTextEqual(
        r"""
            +  S -> b | a AB b BC
            + AB -> &
            + BC -> &
        """, firstGrammar )

    def test_grammarTreeParsingABandB(self):
        grammar = \
        r"""
            S -> aABb BC | b
            AB -> &
            BC -> &
        """
        firstGrammar = ChomskyGrammar.parse( grammar )
        new_tree = ChomskyGrammarTreeTransformer().transform( firstGrammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   S
            +   productions
            +     a AB b BC
            +     b
            +   new_line
            +
            +   AB
            +   productions  &
            +   new_line
            +
            +   BC
            +   productions  &
        """, new_tree.pretty() )

    def test_grammarRawTreeParsingABandB(self):
        grammar = \
        r"""
            S -> aABb BC | b
            AB -> &
            BC -> &
        """
        firstGrammar = ChomskyGrammar.parse( grammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   start_symbol
            +     production
            +       token
            +         non_terminals  S
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  a
            +       token
            +         non_terminals
            +           A
            +           B
            +       token
            +         terminals  b
            +
            +       token
            +         non_terminals
            +           B
            +           C
            +
            +     production
            +
            +       token
            +         terminals  b
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals
            +           A
            +           B
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  &
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals
            +           B
            +           C
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  &
        """, firstGrammar.pretty() )

    def test_grammarInputParsingEmptyEpsilon(self):
        grammar = \
        r"""
             S ->
            SS -> S |
        """
        firstGrammar = ChomskyGrammar.load_from_text_lines( grammar )

        self.assertTextEqual(
        r"""
            +  S -> &
            + SS -> & | S
        """, firstGrammar )

    def test_grammarTreeParsingEmptyEpsilon(self):
        grammar = \
        r"""
             S ->
            SS -> S |
        """
        firstGrammar = ChomskyGrammar.parse( grammar )
        new_tree = ChomskyGrammarTreeTransformer().transform( firstGrammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   S
            +   productions
            +   new_line
            +
            +   SS
            +   productions
            +     S
        """, new_tree.pretty() )

    def test_grammarRawTreeParsingEmptyEpsilon(self):
        grammar = \
        r"""
             S ->
            SS -> S |
        """
        firstGrammar = ChomskyGrammar.parse( grammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   start_symbol
            +     production
            +       token
            +         non_terminals  S
            +
            +   productions
            +     production
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals
            +           S
            +           S
            +
            +   productions
            +     production
            +
            +       token
            +         non_terminals  S
            +
            +     production
        """, firstGrammar.pretty() )

    def test_grammarInputParsingSSandEpsilon(self):
        grammar = \
        r"""
            S   -> SS SSS | &
            SS  -> &
            SSS -> &
        """
        firstGrammar = ChomskyGrammar.load_from_text_lines( grammar )

        self.assertTextEqual(
        r"""
            +   S -> & | SS SSS
            +  SS -> &
            + SSS -> &
        """, firstGrammar )

    def test_grammarTreeParsingSSandEpsilon(self):
        grammar = \
        r"""
            S   -> SS SSS | &
            SS  -> &
            SSS -> &
        """
        firstGrammar = ChomskyGrammar.parse( grammar )
        new_tree = ChomskyGrammarTreeTransformer().transform( firstGrammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   S
            +   productions
            +     SS SSS
            +     &
            +   new_line
            +
            +   SS
            +   productions  &
            +   new_line
            +
            +   SSS
            +   productions  &
        """, new_tree.pretty() )

    def test_grammarRawTreeParsingSSandEpsilon(self):
        grammar = \
        r"""
            S   -> SS SSS | &
            SS  -> &
            SSS -> &
        """
        firstGrammar = ChomskyGrammar.parse( grammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   start_symbol
            +     production
            +       token
            +         non_terminals  S
            +
            +
            +
            +   productions
            +     production
            +
            +       token
            +         non_terminals
            +           S
            +           S
            +
            +       token
            +         non_terminals
            +           S
            +           S
            +           S
            +
            +     production
            +
            +       token
            +         terminals  &
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals
            +           S
            +           S
            +
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  &
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals
            +           S
            +           S
            +           S
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  &
        """, firstGrammar.pretty() )

    def test_grammarInputParsingDoubleSSSstart(self):
        grammar = \
        r"""
            SS SS -> a
        """

        with self.assertRaisesRegex( ValueError, "The start symbol must to be a Production with length 1! SS SS" ):
            firstGrammar = ChomskyGrammar.load_from_text_lines( grammar )

    def test_grammarTreeParsingDoubleSSSstart(self):
        grammar = \
        r"""
            SS SS -> a
        """
        firstGrammar = ChomskyGrammar.parse( grammar )
        new_tree = ChomskyGrammarTreeTransformer().transform( firstGrammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   SS SS
            +   productions  a
        """, new_tree.pretty() )

    def test_grammarRawTreeParsingDoubleSSSstart(self):
        grammar = \
        r"""
            SS SS -> a
        """
        firstGrammar = ChomskyGrammar.parse( grammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   start_symbol
            +     production
            +       token
            +         non_terminals
            +           S
            +           S
            +
            +       token
            +         non_terminals
            +           S
            +           S
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  a
        """, firstGrammar.pretty() )

    def test_grammarInputSingleAmbiguityCase(self):
        grammar = \
        r"""
            S -> S S | &
        """
        firstGrammar = ChomskyGrammar.load_from_text_lines( grammar )

        self.assertTextEqual(
        r"""
            + S -> & | S S
        """, firstGrammar )

    def test_grammarTreeSingleAmbiguityCase(self):
        grammar = \
        r"""
            S -> S S | &
        """
        firstGrammar = ChomskyGrammar.parse( grammar )
        new_tree = ChomskyGrammarTreeTransformer().transform( firstGrammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   S
            +   productions
            +     S S
            +     &
        """, new_tree.pretty() )

    def test_grammarRawTreeSingleAmbiguityCase(self):
        grammar = \
        r"""
            S -> S S | &
        """
        firstGrammar = ChomskyGrammar.parse( grammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   start_symbol
            +     production
            +       token
            +         non_terminals  S
            +
            +   productions
            +     production
            +
            +       token
            +         non_terminals  S
            +
            +       token
            +         non_terminals  S
            +
            +     production
            +
            +       token
            +         terminals  &
        """, firstGrammar.pretty() )

    def test_grammarInputSpecialSymbolsList3Exercice7ItemA(self):
        grammar = \
        r"""
            P -> D L | &
            C -> V = exp | id ( E )
            D -> d D | &
            E -> exp , E | exp
            L -> L ; C | C
            V -> id [ E ] | id
        """
        firstGrammar = ChomskyGrammar.load_from_text_lines( grammar )

        self.assertTextEqual(
        r"""
            + P -> & | D L
            + C -> V = exp | id ( E )
            + D -> & | d D
            + E -> exp | exp , E
            + L -> C | L ; C
            + V -> id | id [ E ]
        """, firstGrammar )

    def test_grammarTreeSpecialSymbolsList3Exercice7ItemA(self):
        grammar = \
        r"""
            P -> D L | &
            C -> V = exp | id ( E )
            D -> d D | &
            E -> exp , E | exp
            L -> L ; C | C
            V -> id [ E ] | id
        """
        firstGrammar = ChomskyGrammar.parse( grammar )
        new_tree = ChomskyGrammarTreeTransformer().transform( firstGrammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   P
            +   productions
            +     D L
            +     &
            +   new_line
            +
            +   C
            +   productions
            +     V = exp
            +     id ( E )
            +   new_line
            +
            +   D
            +   productions
            +     d D
            +     &
            +   new_line
            +
            +   E
            +   productions
            +     exp , E
            +     exp
            +   new_line
            +
            +   L
            +   productions
            +     L ; C
            +     C
            +   new_line
            +
            +   V
            +   productions
            +     id [ E ]
            +     id
        """, new_tree.pretty() )

    def test_grammarRawTreeSpecialSymbolsList3Exercice7ItemA(self):
        grammar = \
        r"""
            P -> D L | &
            C -> V = exp | id ( E )
            D -> d D | &
            E -> exp , E | exp
            L -> L ; C | C
            V -> id [ E ] | id
        """
        firstGrammar = ChomskyGrammar.parse( grammar )

        self.assertTextEqual(
        r"""
            + grammar
            +   start_symbol
            +     production
            +       token
            +         non_terminals  P
            +
            +   productions
            +     production
            +
            +       token
            +         non_terminals  D
            +
            +       token
            +         non_terminals  L
            +
            +     production
            +
            +       token
            +         terminals  &
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals  C
            +
            +   productions
            +     production
            +
            +       token
            +         non_terminals  V
            +
            +       token
            +         terminals  =
            +
            +       token
            +         terminals
            +           e
            +           x
            +           p
            +
            +     production
            +
            +       token
            +         terminals
            +           i
            +           d
            +
            +       token
            +         terminals  (
            +
            +       token
            +         non_terminals  E
            +
            +       token
            +         terminals  )
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals  D
            +
            +   productions
            +     production
            +
            +       token
            +         terminals  d
            +
            +       token
            +         non_terminals  D
            +
            +     production
            +
            +       token
            +         terminals  &
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals  E
            +
            +   productions
            +     production
            +
            +       token
            +         terminals
            +           e
            +           x
            +           p
            +
            +       token
            +         terminals  ,
            +
            +       token
            +         non_terminals  E
            +
            +     production
            +
            +       token
            +         terminals
            +           e
            +           x
            +           p
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals  L
            +
            +   productions
            +     production
            +
            +       token
            +         non_terminals  L
            +
            +       token
            +         terminals  ;
            +
            +       token
            +         non_terminals  C
            +
            +     production
            +
            +       token
            +         non_terminals  C
            +   new_line
            +
            +   start_symbol
            +     production
            +       token
            +         non_terminals  V
            +
            +   productions
            +     production
            +
            +       token
            +         terminals
            +           i
            +           d
            +
            +       token
            +         terminals  [
            +
            +       token
            +         non_terminals  E
            +
            +       token
            +         terminals  ]
            +
            +     production
            +
            +       token
            +         terminals
            +           i
            +           d
        """, firstGrammar.pretty() )


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
            + Production locked: True, str: A B C D, len: 4, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;, NonTerminal locked: True, str: B, len: 1, sequence: 2;, NonTerminal locked: True, str:
            + C, len: 1, sequence: 3;, NonTerminal locked: True, str: D, len: 1, sequence: 4;], sequence: 4;
        """, wrap_text( repr( production ), wrap=100 ) )

    def test_combinationNonTerminalRemovalSymbolFromABCD(self):
        symbols = [self.ntA, self.ntB, self.ntC, self.ntD]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: &, len: 0, symbols: [Terminal locked: True, str: &, len: 0, sequence:
            + 1;], sequence: 1;
            + , Production locked: True, str: A, len: 1, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;], sequence: 1;
            + , Production locked: True, str: B, len: 1, symbols: [NonTerminal locked: True, str: B, len: 1,
            + sequence: 1;], sequence: 1;
            + , Production locked: True, str: C, len: 1, symbols: [NonTerminal locked: True, str: C, len: 1,
            + sequence: 1;], sequence: 1;
            + , Production locked: True, str: D, len: 1, symbols: [NonTerminal locked: True, str: D, len: 1,
            + sequence: 1;], sequence: 1;
            + , Production locked: True, str: A B, len: 2, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;, NonTerminal locked: True, str: B, len: 1, sequence: 2;], sequence: 2;
            + , Production locked: True, str: A C, len: 2, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;, NonTerminal locked: True, str: C, len: 1, sequence: 2;], sequence: 2;
            + , Production locked: True, str: A D, len: 2, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;, NonTerminal locked: True, str: D, len: 1, sequence: 2;], sequence: 2;
            + , Production locked: True, str: B C, len: 2, symbols: [NonTerminal locked: True, str: B, len: 1,
            + sequence: 1;, NonTerminal locked: True, str: C, len: 1, sequence: 2;], sequence: 2;
            + , Production locked: True, str: B D, len: 2, symbols: [NonTerminal locked: True, str: B, len: 1,
            + sequence: 1;, NonTerminal locked: True, str: D, len: 1, sequence: 2;], sequence: 2;
            + , Production locked: True, str: C D, len: 2, symbols: [NonTerminal locked: True, str: C, len: 1,
            + sequence: 1;, NonTerminal locked: True, str: D, len: 1, sequence: 2;], sequence: 2;
            + , Production locked: True, str: A B C, len: 3, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;, NonTerminal locked: True, str: B, len: 1, sequence: 2;, NonTerminal locked: True, str:
            + C, len: 1, sequence: 3;], sequence: 3;
            + , Production locked: True, str: A B D, len: 3, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;, NonTerminal locked: True, str: B, len: 1, sequence: 2;, NonTerminal locked: True, str:
            + D, len: 1, sequence: 3;], sequence: 3;
            + , Production locked: True, str: A C D, len: 3, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;, NonTerminal locked: True, str: C, len: 1, sequence: 2;, NonTerminal locked: True, str:
            + D, len: 1, sequence: 3;], sequence: 3;
            + , Production locked: True, str: B C D, len: 3, symbols: [NonTerminal locked: True, str: B, len: 1,
            + sequence: 1;, NonTerminal locked: True, str: C, len: 1, sequence: 2;, NonTerminal locked: True, str:
            + D, len: 1, sequence: 3;], sequence: 3;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationNonTerminalRemovalSymbolFromABC(self):
        symbols = [self.ntA, self.ntB, self.ntC]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: &, len: 0, symbols: [Terminal locked: True, str: &, len: 0, sequence:
            + 1;], sequence: 1;
            + , Production locked: True, str: A, len: 1, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;], sequence: 1;
            + , Production locked: True, str: B, len: 1, symbols: [NonTerminal locked: True, str: B, len: 1,
            + sequence: 1;], sequence: 1;
            + , Production locked: True, str: C, len: 1, symbols: [NonTerminal locked: True, str: C, len: 1,
            + sequence: 1;], sequence: 1;
            + , Production locked: True, str: A B, len: 2, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;, NonTerminal locked: True, str: B, len: 1, sequence: 2;], sequence: 2;
            + , Production locked: True, str: A C, len: 2, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;, NonTerminal locked: True, str: C, len: 1, sequence: 2;], sequence: 2;
            + , Production locked: True, str: B C, len: 2, symbols: [NonTerminal locked: True, str: B, len: 1,
            + sequence: 1;, NonTerminal locked: True, str: C, len: 1, sequence: 2;], sequence: 2;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationNonTerminalRemovalSymbolFromAB(self):
        symbols = [self.ntA, self.ntB]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: &, len: 0, symbols: [Terminal locked: True, str: &, len: 0, sequence:
            + 1;], sequence: 1;
            + , Production locked: True, str: A, len: 1, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;], sequence: 1;
            + , Production locked: True, str: B, len: 1, symbols: [NonTerminal locked: True, str: B, len: 1,
            + sequence: 1;], sequence: 1;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationNonTerminalRemovalSymbolFromA(self):
        symbols = [self.ntA]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: &, len: 0, symbols: [Terminal locked: True, str: &, len: 0, sequence:
            + 1;], sequence: 1;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationNonTerminalRemovalSymbolFromAa(self):
        symbols = [self.ntA, self.ta]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: a, len: 1, symbols: [Terminal locked: True, str: a, len: 1, sequence:
            + 1;], sequence: 1;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationNonTerminalRemovalSymbolFromBAa(self):
        symbols = [self.ntB, self.ntA, self.ta.new()]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: a, len: 1, symbols: [Terminal locked: True, str: a, len: 1, sequence:
            + 1;], sequence: 1;
            + , Production locked: True, str: A a, len: 2, symbols: [NonTerminal locked: True, str: A, len: 1,
            + sequence: 1;, Terminal locked: True, str: a, len: 1, sequence: 2;], sequence: 2;
            + , Production locked: True, str: B a, len: 2, symbols: [NonTerminal locked: True, str: B, len: 1,
            + sequence: 1;, Terminal locked: True, str: a, len: 1, sequence: 2;], sequence: 2;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationNonTerminalRemovalSymbolFromaAa(self):
        symbols = [self.ta, self.ntA, self.ta.new()]
        production = Production( symbols, lock=True )

        self.assertTextEqual(
        r"""
            + [Production locked: True, str: a a, len: 2, symbols: [Terminal locked: True, str: a, len: 1,
            + sequence: 1;, Terminal locked: True, str: a, len: 1, sequence: 2;], sequence: 2;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations( symbols ) ), wrap=100 ) )

    def test_combinationFilterNonTerminalsFromaAa(self):
        symbols = [self.ta, self.ntA, self.ta.new()]
        production = Production( symbols )
        production.filter_non_terminals( symbols, [] )

        self.assertTextEqual(
        r"""
            + [Terminal locked: True, str: a, len: 1, sequence: 1;, Terminal locked: True, str: a, len: 1, sequence: 2;]
        """, sort_alphabetically_and_by_length( production ) )

    def test_combinationFilterNonTerminalsFromAa(self):
        symbols = [self.ntA, self.ta]
        production = Production( symbols )
        production.filter_non_terminals( symbols, [] )

        self.assertTextEqual(
        r"""
            + [Terminal locked: True, str: a, len: 1, sequence: 1;]
        """, sort_alphabetically_and_by_length( production ) )


class TestDynamicIterationDict(TestingUtilities):

    def test_removalAtBeginingWithIterationAtEnd(self):
        elements = DynamicIterationDict([0, 1, 2, 3, 4, 5, 6, 7], index=True)
        current_index = -1
        iterated_elements = []

        for element in elements:
            current_index += 1

            if current_index == 2:
                elements.remove( 1 )

            if current_index == 5:
                elements.add( 8 )

            iterated_elements.append( element )

        self.assertTextEqual(
        r"""
            + {0, 0: None, 2, 2: None, 3, 3: None, 4, 4: None, 5, 5: None, 6, 6: None, 7, 7: None, 8, 8: None}
        """, wrap_text( elements, wrap=0 ) )

        self.assertTextEqual(
        r"""
            + [0, 1, 2, 3, 4, 5, 6, 7, 8]
        """, wrap_text( iterated_elements, wrap=0 ) )

        new_elements = elements.copy()
        elements.trim_indexes_unsorted()
        new_elements.trim_indexes_sorted()

        self.assertTextEqual(
        r"""
            + {0, 0: None, 8, 1: None, 2, 2: None, 3, 3: None, 4, 4: None, 5, 5: None, 6, 6: None, 7, 7: None}
        """, wrap_text( elements, wrap=0 ) )

        self.assertTextEqual(
        r"""
            + {0, 0: None, 2, 1: None, 3, 2: None, 4, 3: None, 5, 4: None, 6, 5: None, 7, 6: None, 8, 7: None}
        """, wrap_text( new_elements, wrap=0 ) )

    def test_recursiveIterationCreation(self):
        elements = DynamicIterationDict([0, 1, 2])
        current_index1 = -1
        iterated_elements = []

        for element1 in elements:
            current_index1 += 1
            current_index2 = -1

            for element2 in elements:
                current_index2 += 1
                iterated_elements.append( ( element1, element2, repr( elements ) ) )

        self.assertTextEqual(
        r"""
            + (0, 0, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -2,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (0, 1, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -2,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (0, 2, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -2,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (1, 0, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -3,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (1, 1, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -3,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (1, 2, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -3,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (2, 0, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -4,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (2, 1, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -4,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (2, 2, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -4,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
        """, wrap_text( "".join( [str( item ) + "\n" for item in iterated_elements] ), wrap=105, indent="       " ) )

    def test_recursiveIterationCreationDynamicItemsAddition(self):
        elements = DynamicIterationDict([0, 1, 2])
        current_index1 = -1
        iterated_elements = []

        for element1 in elements:
            current_index1 += 1
            current_index2 = -1

            if current_index1 == 1:
                elements.add( 3 )

            for element2 in elements:
                current_index2 += 1
                iterated_elements.append( ( element1, element2, repr( elements ) ) )

        self.assertTextEqual(
        r"""
            + (0, 0, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -2,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (0, 1, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -2,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (0, 2, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -2,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (1, 0, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        set(), filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2, 3: 3}, new_items_skip_count: -3,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (1, 1, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        set(), filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2, 3: 3}, new_items_skip_count: -3,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (1, 2, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        set(), filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2, 3: 3}, new_items_skip_count: -3,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (1, 3, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        set(), filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2, 3: 3}, new_items_skip_count: -3,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (2, 0, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        set(), filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2, 3: 3}, new_items_skip_count: -4,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (2, 1, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        set(), filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2, 3: 3}, new_items_skip_count: -4,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (2, 2, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        set(), filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2, 3: 3}, new_items_skip_count: -4,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (2, 3, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        set(), filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2, 3: 3}, new_items_skip_count: -4,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (3, 0, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        set(), filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2, 3: 3}, new_items_skip_count: -5,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (3, 1, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        set(), filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2, 3: 3}, new_items_skip_count: -5,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (3, 2, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        set(), filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2, 3: 3}, new_items_skip_count: -5,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (3, 3, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        set(), filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2, 3: 3}, new_items_skip_count: -5,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
        """, wrap_text( "".join( [str( item ) + "\n" for item in iterated_elements] ), wrap=105, indent="       " ) )

    def test_recursiveIterationCreationDynamicItemsRemoval(self):
        elements = DynamicIterationDict([0, 1, 2])
        current_index1 = -1
        iterated_elements = []

        for element1 in elements:
            current_index1 += 1
            current_index2 = -1

            if current_index1 == 1:
                elements.remove( 0 )

            if current_index1 == 2:
                elements.add( 3 )

            for element2 in elements:
                current_index2 += 1
                iterated_elements.append( ( element1, element2, repr( elements ) ) )

        self.assertTextEqual(
        r"""
            + (0, 0, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -2,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (0, 1, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -2,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (0, 2, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -2,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (1, 1, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: {0},
            +        filled_slots: set(), items_dictionary: {1: 1, 2: 2}, new_items_skip_count: -3,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (1, 2, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: {0},
            +        filled_slots: set(), items_dictionary: {1: 1, 2: 2}, new_items_skip_count: -3,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (2, 1, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -4,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (2, 2, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -4,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (2, 3, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -4,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (3, 1, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -5,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (3, 2, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -5,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (3, 3, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -5,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
        """, wrap_text( "".join( [str( item ) + "\n" for item in iterated_elements] ), wrap=105, indent="       " ) )

    def test_recursiveIterationCreationDynamicItemsRemovalDouble(self):
        elements = DynamicIterationDict([0, 1, 2])
        current_index1 = -1
        iterated_elements = []

        for element1 in elements:
            current_index1 += 1
            current_index2 = -1

            for element2 in elements:
                current_index2 += 1

                if current_index2 == 1:
                    elements.discard( 0 )

                if current_index2 == 2:
                    elements.add( 3 )

                iterated_elements.append( ( element1, element2, repr( elements ) ) )

        self.assertTextEqual(
        r"""
            + (0, 0, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {0: 0, 1: 1, 2: 2}, new_items_skip_count: -2,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (0, 1, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: {0},
            +        filled_slots: set(), items_dictionary: {1: 1, 2: 2}, new_items_skip_count: -2,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (0, 2, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -2,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (0, 3, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -2,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (1, 1, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -3,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (1, 2, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -3,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (1, 3, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -3,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (2, 1, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -4,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (2, 2, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -4,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (2, 3, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -4,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (3, 1, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -5,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (3, 2, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -5,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
            + (3, 3, 'DynamicIterationDict keys_list: [0, 1, 2, 3], values_list: [None, None, None, None], empty_slots:
            +        {0}, filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 3}, new_items_skip_count: -5,
            +        new_items_skip_stack: [], maximum_iterable_index: [0];')
        """, wrap_text( "".join( [str( item ) + "\n" for item in iterated_elements] ), wrap=105, indent="       " ) )

    def test_recursiveIterationCreationDynamicItemsIgnoring4NewItems(self):
        elements = DynamicIterationDict([0, 1, 2])
        current_index1 = -1
        iterated_elements = []

        for element1 in elements(4):
            current_index1 += 1
            current_index2 = -1

            if current_index1 == 0:
                elements.remove( 0 )

            if current_index1 == 1:
                elements.add( 3 )

            for element2 in elements:
                current_index2 += 1
                iterated_elements.append( ( element1, element2, repr( elements ) ) )

        self.assertTextEqual(
        r"""
            + (0, 1, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: {0},
            +        filled_slots: set(), items_dictionary: {1: 1, 2: 2}, new_items_skip_count: 3,
            +        new_items_skip_stack: [], maximum_iterable_index: [3];')
            + (0, 2, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: {0},
            +        filled_slots: set(), items_dictionary: {1: 1, 2: 2}, new_items_skip_count: 3,
            +        new_items_skip_stack: [], maximum_iterable_index: [3];')
            + (1, 1, 'DynamicIterationDict keys_list: [3, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: {0}, items_dictionary: {1: 1, 2: 2, 3: 0}, new_items_skip_count: 2,
            +        new_items_skip_stack: [], maximum_iterable_index: [3];')
            + (1, 2, 'DynamicIterationDict keys_list: [3, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: {0}, items_dictionary: {1: 1, 2: 2, 3: 0}, new_items_skip_count: 2,
            +        new_items_skip_stack: [], maximum_iterable_index: [3];')
            + (2, 1, 'DynamicIterationDict keys_list: [3, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: {0}, items_dictionary: {1: 1, 2: 2, 3: 0}, new_items_skip_count: 1,
            +        new_items_skip_stack: [], maximum_iterable_index: [3];')
            + (2, 2, 'DynamicIterationDict keys_list: [3, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: {0}, items_dictionary: {1: 1, 2: 2, 3: 0}, new_items_skip_count: 1,
            +        new_items_skip_stack: [], maximum_iterable_index: [3];')
        """, wrap_text( "".join( [str( item ) + "\n" for item in iterated_elements] ), wrap=105, indent="       " ) )

    def test_recursiveIterationCreationDynamicItemsIgnoring1NewItems(self):
        elements = DynamicIterationDict([0, 1, 2])
        current_index1 = -1
        iterated_elements = []

        for element1 in elements(1):
            current_index1 += 1
            current_index2 = -1

            if current_index1 == 0:
                elements.remove( 0 )

            if current_index1 == 1:
                elements.add( 3 )

            for element2 in elements(1):
                current_index2 += 1
                iterated_elements.append( ( element1, element2, repr( elements ) ) )

        self.assertTextEqual(
        r"""
            + (0, 1, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: {0},
            +        filled_slots: set(), items_dictionary: {1: 1, 2: 2}, new_items_skip_count: 1,
            +        new_items_skip_stack: [], maximum_iterable_index: [3];')
            + (0, 2, 'DynamicIterationDict keys_list: [0, 1, 2], values_list: [None, None, None], empty_slots: {0},
            +        filled_slots: set(), items_dictionary: {1: 1, 2: 2}, new_items_skip_count: 1,
            +        new_items_skip_stack: [], maximum_iterable_index: [3];')
            + (1, 3, 'DynamicIterationDict keys_list: [3, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 0}, new_items_skip_count: 1,
            +        new_items_skip_stack: [], maximum_iterable_index: [3];')
            + (1, 1, 'DynamicIterationDict keys_list: [3, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 0}, new_items_skip_count: 1,
            +        new_items_skip_stack: [], maximum_iterable_index: [3];')
            + (1, 2, 'DynamicIterationDict keys_list: [3, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 0}, new_items_skip_count: 1,
            +        new_items_skip_stack: [], maximum_iterable_index: [3];')
            + (2, 3, 'DynamicIterationDict keys_list: [3, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 0}, new_items_skip_count: 1,
            +        new_items_skip_stack: [], maximum_iterable_index: [3];')
            + (2, 1, 'DynamicIterationDict keys_list: [3, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 0}, new_items_skip_count: 1,
            +        new_items_skip_stack: [], maximum_iterable_index: [3];')
            + (2, 2, 'DynamicIterationDict keys_list: [3, 1, 2], values_list: [None, None, None], empty_slots: set(),
            +        filled_slots: set(), items_dictionary: {1: 1, 2: 2, 3: 0}, new_items_skip_count: 1,
            +        new_items_skip_stack: [], maximum_iterable_index: [3];')
        """, wrap_text( "".join( [str( item ) + "\n" for item in iterated_elements] ), wrap=105, indent="       " ) )


if __name__ == "__main__":
    unittest.main()

