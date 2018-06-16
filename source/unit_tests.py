#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import lark

import unittest
from natsort import natsorted
from collections import OrderedDict

from grammar.grammar import ChomskyGrammar

from grammar.utilities import wrap_text
from grammar.utilities import getCleanSpaces
from grammar.utilities import dictionary_to_string
from grammar.utilities import sort_alphabetically_and_by_length

from grammar.symbols import Terminal
from grammar.symbols import NonTerminal

from grammar.production import Production
from grammar.production import epsilon_production
from grammar.production import epsilon_terminal
from grammar.lockable_type import LockableType
from grammar.tree_transformer import ChomskyGrammarTreeTransformer

from grammar.testing_utilities import TestingUtilities


class TestProduction(TestingUtilities):
    """
        Tests the Production class.
    """

    def setUp(self):
        """
            Creates basic non terminal's for usage.
        """
        super().setUp()
        self.ntA = NonTerminal( "A" )
        self.ntB = NonTerminal( "B" )
        self.ntC = NonTerminal( "C" )
        self.ntD = NonTerminal( "D" )
        LockableType._USE_STRING = True

    def test_productionNonTerminalRemoval1SymbolABCD(self):
        LockableType._USE_STRING = False
        production = Production( symbols=[self.ntA, self.ntB, self.ntC, self.ntD], lock=True )

        self.assertTextEqual(
        """
            + [Production locked: True, str: A, symbols: [NonTerminal locked: True, str: A, sequence: 1,
            + has_epsilon: False, len: 1;], sequence: 4, has_epsilon: False, len: 1;
            + , Production locked: True, str: B, symbols: [NonTerminal locked: True, str: B, sequence: 2,
            + has_epsilon: False, len: 1;], sequence: 4, has_epsilon: False, len: 1;
            + , Production locked: True, str: C, symbols: [NonTerminal locked: True, str: C, sequence: 3,
            + has_epsilon: False, len: 1;], sequence: 4, has_epsilon: False, len: 1;
            + , Production locked: True, str: D, symbols: [NonTerminal locked: True, str: D, sequence: 4,
            + has_epsilon: False, len: 1;], sequence: 4, has_epsilon: False, len: 1;
            + , Production locked: True, str: A B, symbols: [NonTerminal locked: True, str: A, sequence: 1,
            + has_epsilon: False, len: 1;, NonTerminal locked: True, str: B, sequence: 2, has_epsilon: False, len:
            + 1;], sequence: 4, has_epsilon: False, len: 2;
            + , Production locked: True, str: A C, symbols: [NonTerminal locked: True, str: A, sequence: 1,
            + has_epsilon: False, len: 1;, NonTerminal locked: True, str: C, sequence: 3, has_epsilon: False, len:
            + 1;], sequence: 4, has_epsilon: False, len: 2;
            + , Production locked: True, str: A D, symbols: [NonTerminal locked: True, str: A, sequence: 1,
            + has_epsilon: False, len: 1;, NonTerminal locked: True, str: D, sequence: 4, has_epsilon: False, len:
            + 1;], sequence: 4, has_epsilon: False, len: 2;
            + , Production locked: True, str: B C, symbols: [NonTerminal locked: True, str: B, sequence: 2,
            + has_epsilon: False, len: 1;, NonTerminal locked: True, str: C, sequence: 3, has_epsilon: False, len:
            + 1;], sequence: 4, has_epsilon: False, len: 2;
            + , Production locked: True, str: B D, symbols: [NonTerminal locked: True, str: B, sequence: 2,
            + has_epsilon: False, len: 1;, NonTerminal locked: True, str: D, sequence: 4, has_epsilon: False, len:
            + 1;], sequence: 4, has_epsilon: False, len: 2;
            + , Production locked: True, str: C D, symbols: [NonTerminal locked: True, str: C, sequence: 3,
            + has_epsilon: False, len: 1;, NonTerminal locked: True, str: D, sequence: 4, has_epsilon: False, len:
            + 1;], sequence: 4, has_epsilon: False, len: 2;
            + , Production locked: True, str: A B C, symbols: [NonTerminal locked: True, str: A, sequence: 1,
            + has_epsilon: False, len: 1;, NonTerminal locked: True, str: B, sequence: 2, has_epsilon: False, len:
            + 1;, NonTerminal locked: True, str: C, sequence: 3, has_epsilon: False, len: 1;], sequence: 4,
            + has_epsilon: False, len: 3;
            + , Production locked: True, str: A B D, symbols: [NonTerminal locked: True, str: A, sequence: 1,
            + has_epsilon: False, len: 1;, NonTerminal locked: True, str: B, sequence: 2, has_epsilon: False, len:
            + 1;, NonTerminal locked: True, str: D, sequence: 4, has_epsilon: False, len: 1;], sequence: 4,
            + has_epsilon: False, len: 3;
            + , Production locked: True, str: A C D, symbols: [NonTerminal locked: True, str: A, sequence: 1,
            + has_epsilon: False, len: 1;, NonTerminal locked: True, str: C, sequence: 3, has_epsilon: False, len:
            + 1;, NonTerminal locked: True, str: D, sequence: 4, has_epsilon: False, len: 1;], sequence: 4,
            + has_epsilon: False, len: 3;
            + , Production locked: True, str: B C D, symbols: [NonTerminal locked: True, str: B, sequence: 2,
            + has_epsilon: False, len: 1;, NonTerminal locked: True, str: C, sequence: 3, has_epsilon: False, len:
            + 1;, NonTerminal locked: True, str: D, sequence: 4, has_epsilon: False, len: 1;], sequence: 4,
            + has_epsilon: False, len: 3;
            + , Production locked: True, str: A B C D, symbols: [NonTerminal locked: True, str: A, sequence: 1,
            + has_epsilon: False, len: 1;, NonTerminal locked: True, str: B, sequence: 2, has_epsilon: False, len:
            + 1;, NonTerminal locked: True, str: C, sequence: 3, has_epsilon: False, len: 1;, NonTerminal locked:
            + True, str: D, sequence: 4, has_epsilon: False, len: 1;], sequence: 4, has_epsilon: False, len: 4;
            + ]
        """, wrap_text( sort_alphabetically_and_by_length( production.combinations() ), wrap=100 ) )

    def test_productionNonTerminalRemoval1SymbolABC(self):
        production = Production( symbols=[self.ntA, self.ntB, self.ntC], lock=True )

        self.assertTextEqual(
        """
            + [A
            + , B
            + , C
            + , A B
            + , A C
            + , B C
            + , A B C
            + ]
        """, sort_alphabetically_and_by_length( production.combinations() ) )

    def test_productionNonTerminalRemoval1SymbolAB(self):
        production = Production( symbols=[self.ntA, self.ntB], lock=True )

        self.assertTextEqual(
        """
            + [A
            + , B
            + , A B
            + ]
        """, sort_alphabetically_and_by_length( production.combinations() ) )

    def test_productionNonTerminalRemoval1SymbolFromA(self):
        production = Production( symbols=[self.ntA], lock=True )

        self.assertTextEqual(
        """
            + [A
            + ]
        """, sort_alphabetically_and_by_length( production.combinations() ) )

    def test_productionABCD(self):
        production = Production( symbols=[self.ntA, self.ntB, self.ntC, self.ntD], lock=True )

        self.assertTextEqual(
        """
            + A B C D
        """, production )


class TestChomskyGrammar(TestingUtilities):
    """
        Tests the Grammar class.
    """

    def tearDown(self):
        LockableType._USE_STRING = True

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

    def test_grammarNonTerminalHasTransitionsWithChapter5FirstExample1(self):
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

        self.assertFalse( firstGrammar.non_terminal_has_transitions_with( non_terminal_S, production_S ) )
        self.assertTrue( firstGrammar.non_terminal_has_transitions_with( non_terminal_S, production_A ) )

    def test_grammarHasOnNonTerminalChapter5FirstExample1(self):
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

    def test_grammarConvertToEpsilonFreeChapter5FirstExample1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        firstGrammar.convert_to_epsilon_free()

        self.assertTextEqual(
        """
        """, firstGrammar )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    def test_grammarIsNotEpsilonFreeChapter5FirstExample1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )

        self.assertFalse( firstGrammar.is_epsilon_free() )

    def test_grammarIsEpsilonFreeChapter5FirstExample1EpsilonFreed(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc | &
            A -> aA | a
            B -> bB | Ad
        """ ) )

        self.assertTrue( firstGrammar.is_epsilon_free() )

    # def test_grammarHasLeftRecursionCalculationOfChapter5FirstExample1(self):
    #     firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
    #     """
    #         S -> Ab | A Bc
    #         A -> aA | &
    #         B -> bB | Ad | &
    #     """ ) )

    #     self.assertTextEqual(
    #     """
    #         not implemented yet
    #     """, dictionary_to_string( firstGrammar.left_recursion() ) )

    #     self.assertFalse( firstGrammar.has_left_recursion() )

    # def test_grammarHasLeftRecursionCalculationOfChapter5FirstExample1(self):
    #     firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
    #     """
    #         S -> Ab | A Bc
    #         A -> aA | &
    #         B -> bB | Ad | &
    #     """ ) )

    #     self.assertTextEqual(
    #     """
    #         not implemented yet
    #     """, dictionary_to_string( firstGrammar.left_recursion() ) )

    #     self.assertFalse( firstGrammar.has_left_recursion() )

    # def test_grammarIsFactoredCalculationOfChapter5FirstExample1(self):
    #     firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
    #     """
    #         S -> Ab | A Bc
    #         A -> aA | &
    #         B -> bB | Ad | &
    #     """ ) )

    #     self.assertTextEqual(
    #     """
    #         not implemented yet
    #     """, dictionary_to_string( firstGrammar.factors() ) )

    #     self.assertFalse( firstGrammar.is_factored() )

    # def test_grammarNonTerminalFirstCalculationOfChapter5FirstExample1(self):
    #     firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
    #     """
    #         S -> Ab | A Bc
    #         A -> aA | &
    #         B -> bB | Ad | &
    #     """ ) )
    #     first_non_terminal = firstGrammar.first_non_terminal()

    #     self.assertTextEqual(
    #     """
    #         not implemented yet
    #     """, dictionary_to_string( first_non_terminal ) )

    def test_grammarFirstCalculationOfChapter5FirstExample1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        first = firstGrammar.first()

        self.assertTextEqual(
        """
            + S: a b c d
            + A: & a
            + B: & a b d
        """, dictionary_to_string( first ) )

    def test_grammarFollowCalculationOfChapter5FirstExample1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            A -> aA | &
            B -> bB | Ad | &
        """ ) )
        follow = firstGrammar.follow()

        self.assertTextEqual(
        """
            + S: $
            + A: $ a b d
            + B: c
        """, dictionary_to_string( follow ) )

    def test_grammarFirstCalculationOfChapter5FollowExample1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A B C
            A -> aA | &
            B -> bB | A Cd
            C -> cC | &
        """ ) )
        first = firstGrammar.first()

        self.assertTextEqual(
        """
            + S: a b c d
            + A: & a
            + B: a b c d
            + C: & c
        """, dictionary_to_string( first ) )

    def test_grammarFollowCalculationOfChapter5FollowExample1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A B C
            A -> aA | &
            B -> bB | A Cd
            C -> cC | &
        """ ) )
        follow = firstGrammar.follow()

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
        first = firstGrammar.first()

        self.assertTextEqual(
        """
            +  E: ( id
            + E': & +
            +  T: ( id
            + T': & *
            +  F: ( id
        """, dictionary_to_string( first ) )

    def test_grammarFollowCalculationOfChapter5FollowExample2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            E  -> T E'
            E' -> + T E' | &
            T  -> F T'
            T' -> * F T' | &
            F  -> ( E ) | id
        """ ) )
        follow = firstGrammar.follow()

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
        first = firstGrammar.first()

        self.assertTextEqual(
        """
            + S: a b e f g
            + A: & a
            + C: c e
            + D: & c d e
            + E: & e
            + F: f g
        """, dictionary_to_string( first ) )

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
        follow = firstGrammar.follow()

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
        first = firstGrammar.first()

        self.assertTextEqual(
        """
            + S: & a b c e
            + A: & a b c
            + B: & a b c
            + C: & c
        """, dictionary_to_string( first ) )

    def test_grammarFollowCalculationOfChapter5FollowExample4(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A C | C e B | B a
            A -> a A | B C
            B -> b B | A B | &
            C -> c C | &
        """ ) )
        # sys.setrecursionlimit( 2000 )
        follow = firstGrammar.follow()

        self.assertTextEqual(
        """
            + S: $
            + A: $ a b c
            + B: $ a b c
            + C: $ a b c e
        """, dictionary_to_string( follow ) )

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

    def test_grammarInvalidNonTerminalException(self):

        with self.assertRaisesRegex( RuntimeError, "Invalid Non Terminal `D` added to the grammar" ):
            firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
            """
                S -> Ab | A Dc
                B -> bB | Ad | &
                A -> aA | &
            """ ) )
            firstGrammar.assure_existing_symbols()

    def test_grammarTransformationTreeParsingParenStarPlusSymbols(self):
        LockableType._USE_STRING = False

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
            + sequence: 1, has_epsilon: False, len: 1;], sequence: 1, has_epsilon: False, len: 0;
            + , Tree(space, []), Tree(space, []), Tree(non_terminals, [Production locked: False, str: , symbols:
            + [NonTerminal locked: True, str: T, sequence: 1, has_epsilon: False, len: 1;, NonTerminal locked:
            + True, str: E', sequence: 2, has_epsilon: False, len: 1;], sequence: 2, has_epsilon: False, len: 0;
            + ]), Tree(end_symbol, [Tree(new_line, [Token(NEWLINE, '\n')])]), Production locked: False, str: ,
            + symbols: [NonTerminal locked: True, str: E', sequence: 1, has_epsilon: False, len: 1;], sequence: 1,
            + has_epsilon: False, len: 0;
            + , Tree(space, []), Tree(non_terminals, [Production locked: False, str: , symbols: [Terminal locked:
            + True, str: +, sequence: 1, has_epsilon: False, len: 1;, NonTerminal locked: True, str: T, sequence:
            + 2, has_epsilon: False, len: 1;, NonTerminal locked: True, str: E', sequence: 3, has_epsilon: False,
            + len: 1;], sequence: 3, has_epsilon: False, len: 0;
            + , Production locked: False, str: , symbols: [Terminal locked: True, str: &, sequence: 1,
            + has_epsilon: True, len: 0;], sequence: 1, has_epsilon: True, len: 0;
            + ]), Tree(end_symbol, [Tree(new_line, [Token(NEWLINE, '\n')])]), Production locked: False, str: ,
            + symbols: [NonTerminal locked: True, str: T, sequence: 1, has_epsilon: False, len: 1;], sequence: 1,
            + has_epsilon: False, len: 0;
            + , Tree(space, []), Tree(space, []), Tree(non_terminals, [Production locked: False, str: , symbols:
            + [NonTerminal locked: True, str: F, sequence: 1, has_epsilon: False, len: 1;, NonTerminal locked:
            + True, str: T', sequence: 2, has_epsilon: False, len: 1;], sequence: 2, has_epsilon: False, len: 0;
            + ]), Tree(end_symbol, [Tree(new_line, [Token(NEWLINE, '\n')])]), Production locked: False, str: ,
            + symbols: [NonTerminal locked: True, str: T', sequence: 1, has_epsilon: False, len: 1;], sequence: 1,
            + has_epsilon: False, len: 0;
            + , Tree(space, []), Tree(non_terminals, [Production locked: False, str: , symbols: [Terminal locked:
            + True, str: *, sequence: 1, has_epsilon: False, len: 1;, NonTerminal locked: True, str: F, sequence:
            + 2, has_epsilon: False, len: 1;, NonTerminal locked: True, str: T', sequence: 3, has_epsilon: False,
            + len: 1;], sequence: 3, has_epsilon: False, len: 0;
            + ]), Tree(end_symbol, [Tree(new_line, [Token(NEWLINE, '\n')])]), Production locked: False, str: ,
            + symbols: [NonTerminal locked: True, str: F, sequence: 1, has_epsilon: False, len: 1;], sequence: 1,
            + has_epsilon: False, len: 0;
            + , Tree(space, []), Tree(space, []), Tree(non_terminals, [Production locked: False, str: , symbols:
            + [Terminal locked: True, str: (, sequence: 1, has_epsilon: False, len: 1;, NonTerminal locked: True,
            + str: E, sequence: 2, has_epsilon: False, len: 1;, Terminal locked: True, str: ), sequence: 3,
            + has_epsilon: False, len: 1;], sequence: 3, has_epsilon: False, len: 0;
            + , Production locked: False, str: , symbols: [Terminal locked: True, str: id, sequence: 1,
            + has_epsilon: False, len: 2;], sequence: 1, has_epsilon: False, len: 0;
            + ])])
        """, wrap_text( firstGrammar, wrap=100 ) )

    def test_grammarTransformationParsingComplexSingleProduction(self):
        LockableType._USE_STRING = False

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
            + sequence: 1, has_epsilon: False, len: 1;], sequence: 1, has_epsilon: False, len: 0;
            + , Tree(space, []), Tree(non_terminals, [Production locked: False, str: , symbols: [Terminal locked:
            + True, str: a, sequence: 1, has_epsilon: False, len: 1;, NonTerminal locked: True, str: AB, sequence:
            + 2, has_epsilon: False, len: 1;, Terminal locked: True, str: bb, sequence: 3, has_epsilon: False,
            + len: 2;, NonTerminal locked: True, str: CC, sequence: 4, has_epsilon: False, len: 1;, Terminal
            + locked: True, str: 1a, sequence: 5, has_epsilon: False, len: 2;, NonTerminal locked: True, str: A,
            + sequence: 6, has_epsilon: False, len: 1;, Terminal locked: True, str: b, sequence: 7, has_epsilon:
            + False, len: 1;, NonTerminal locked: True, str: A, sequence: 8, has_epsilon: False, len: 1;,
            + NonTerminal locked: True, str: BC, sequence: 9, has_epsilon: False, len: 1;], sequence: 9,
            + has_epsilon: False, len: 0;
            + , Production locked: False, str: , symbols: [Terminal locked: True, str: ba, sequence: 1,
            + has_epsilon: False, len: 2;], sequence: 1, has_epsilon: False, len: 0;
            + , Production locked: False, str: , symbols: [Terminal locked: True, str: c, sequence: 1,
            + has_epsilon: False, len: 1;], sequence: 1, has_epsilon: False, len: 0;
            + ])])
        """ ), wrap_text( str( firstGrammar ), wrap=100 ) )

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
            +  S -> a AB bb CC 1a A b A BC | ba | c
            +  A -> &
            + AB -> &
            + BC -> &
            + CC -> &
        """, str( firstGrammar ) )

    def test_grammarInputParsingSymbolMerging(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines(
        """
            S -> a b cd | AccD | Ac cD
            A -> &
            D -> &
        """ )

        self.assertTextEqual(
        """
            + S -> A cc D | abcd
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

    # def test_grammarGenerateSentencesOfnAsSize5(self):
    #     firstGrammar = Grammar.load_from_text_lines(
    #     """
    #         A -> aA | a
    #     """ )
    #     generate_sentences = []
    #     firstGrammar.generate_sentences_of_size_n( 5, generate_sentences )

    #     self.assertTextEqual(
    #     """
    #         + ['a', 'aa', 'aaa', 'aaaa', 'aaaaa']
    #     """, str( generate_sentences ) )


if __name__ == "__main__":
    unittest.main()

