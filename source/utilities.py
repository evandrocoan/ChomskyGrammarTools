#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

import time
import random

import lark
import textwrap

import PyQt5
import unittest

from PyQt5 import QtCore

from time import sleep
from threading import Lock

from debug_tools import getLogger

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, os.path.basename( os.path.dirname( os.path.abspath ( __file__ ) ) ) )

HISTORY_KEY_LINE = "-- Grammar History"


class DynamicIterationSet(object):

    def __init__(self):
        self.iterated_items = set()
        self.non_iterated_items = set()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "%s %s" % ( self.iterated_items, self.non_iterated_items )

    def __contains__(self, key):
        return key in self.iterated_items or key in self.non_iterated_items

    def __len__(self):
        return len( self.iterated_items ) + len( self.non_iterated_items )

    def __iter__(self):

        for item in self.iterated_items:
            self.non_iterated_items.add( item )

        self.iterated_items.clear()
        return self

    def __next__(self):

        for first_element in self.non_iterated_items:
            self.non_iterated_items.discard( first_element )
            break

        else:
            self.iterated_items, self.non_iterated_items = self.non_iterated_items, self.iterated_items
            raise StopIteration

        self.iterated_items.add( first_element )
        return first_element

    def add(self, item):

        if item not in self.iterated_items and item not in self.non_iterated_items:
            self.non_iterated_items.add( item )

    def discard(self, item):
        self.iterated_items.discard( item )
        self.non_iterated_items.discard( item )


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


# An unique identifier for any created LockableType object
initial_hash = random.getrandbits( 32 )


class LockableType(object):
    """
        An object type which can have its attributes changes locked/blocked after its `lock()`
        method being called.

        After locking, ts string representation attribute is going to be saved as an attribute and
        returned when needed.
    """

    _USE_STRING = True
    _EMQUOTE_STRING = False

    def __init__(self):
        """
            How to handle call to __setattr__ from __init__?
            https://stackoverflow.com/questions/3870982/how-to-handle-call-to-setattr-from-init
        """
        super().__setattr__('locked', False)
        global initial_hash

        initial_hash += 1
        self._hash = initial_hash

    def __setattr__(self, name, value):
        """
            Block attributes from being changed after it is activated.
            https://stackoverflow.com/questions/17020115/how-to-use-setattr-correctly-avoiding-infinite-recursion
        """

        if self.locked:
            raise AttributeError( "Attributes cannot be changed after `locked` is set to True! %s" % self.__repr__() )

        else:
            super().__setattr__( name, value )

    def __eq__(self, other):

        if isinstance( self, LockableType ) is isinstance( other, LockableType ):
            return hash( self ) == hash( other )

        raise TypeError( "'=' not supported between instances of '%s' and '%s'" % (
                self.__class__.__name__, other.__class__.__name__ ) )

    def __hash__(self):
        return self._hash

    def __repr__(self):

        if self._USE_STRING:
            string = self.__str__()

            if self._EMQUOTE_STRING:
                return emquote_string( string )

            return string

        return self._get_repr()

    def _get_repr(self):
        valid_attributes = self.__dict__.keys()
        clean_attributes = []

        for attribute in valid_attributes:

            if not attribute.startswith( '_' ):
                clean_attributes.append( "{}: {}".format( attribute, self.__dict__[attribute] ) )

        return "%s %s;" % ( self.__class__.__name__, ", ".join( clean_attributes ) )

    def __str__(self):
        """
            Python does not allow to dynamically/monkey patch its build in functions. Then, we create
            out own function and call it from the built-in function.
        """
        return self._str()

    def _str(self):

        if self._USE_STRING:
            return super().__str__()

        return self._get_repr()

    def __len__(self):
        """
            Python does not allow to dynamically/monkey patch its build in functions. Then, we create
            out own function and call it from the built-in function.
        """
        return self._len()

    def _len(self):
        raise TypeError( "object of type '%s' has no len()" % self.__class__.__name__ )

    def lock(self):
        """
            Block further changes to this object attributes and save its string representation for
            faster access.
        """

        if self.locked:
            return

        self.str = str( self )
        self._str = lambda : self.str

        self._hash = hash( self._str() )
        self.locked = True


class ChomskyGrammarSymbol(LockableType):
    """
        General representation for a ChomskyGrammar symbol.

        After locking, its length representation is going to be saved as an attribute and returned
        when needed.
    """

    def __init__(self, symbols, sequence=0, lock=False):
        """
            A full featured Chomsky Grammar symbol able to compose a production or start symbol.

            `symbols` a string representing this symbol
            `sequence` is a integer representing the symbol sort order in a production.
            `lock` if True, the object will be immediately locked upon creation.
        """
        super().__init__()
        self.str = str( symbols )

        self.check_consistency()
        self.sequence = sequence
        self.has_epsilon = False

        if lock:
            self.lock()

    def check_consistency(self):
        """
            Assures the symbol has meaning, i.e., is not empty.
        """

        if not self.str:
            raise RuntimeError( "Invalid symbol creation! Symbol with no length: `%s` (%s)" % self.str, sequence )

    def __lt__(self, other):

        if isinstance( other, LockableType ):
            return str( self ) < str( other )

        raise TypeError( "'<' not supported between instances of '%s' and '%s'" % (
                self.__class__.__name__, other.__class__.__name__ ) )

    def _len(self):
        length = len( self.str )

        for symbol in self.str:

            if symbol == '&':
                length -= 1
                self.has_epsilon = True

        return length

    def _str(self):
        return self.str

    def lock(self):
        """
            Block further changes to this object attributes and save its length for faster access.
        """

        if self.locked:
            return

        self.len = len( self )
        self._len = lambda : self.len

        self.trim_epsilons()
        self.check_consistency()
        super().lock()

    def trim_epsilons(self):
        """
            Merges the epsilon symbol with other symbols, because the epsilon symbol has not
            meaning, unless it is alone.
        """

        if len( self ):
            new_symbols = []

            for symbol in self.str:

                if symbol != '&':
                    new_symbols.append( symbol )

            self.str = "".join( new_symbols )

        else:
            self.str = self.str[0]


class Terminal(ChomskyGrammarSymbol):
    """
        Represents a terminal symbol on an ChomskyGrammar.
    """
    pass


class NonTerminal(ChomskyGrammarSymbol):
    """
        Represents a non terminal symbol on an ChomskyGrammar.
    """
    def _len(self):
        return 1


class Production(LockableType):

    def __init__(self, sequence=0, symbols=[], lock=False):
        """
            A full featured Chomsky Grammar production.

            `sequence` the index of the first symbol of the symbol's sequence
            `symbols` a list of initial symbols to add to the production
            `lock` if True, the object will be immediately locked upon creation
        """
        super().__init__()
        self.symbols = []

        if not isinstance( sequence, int ):
            raise RuntimeError( "The sequence parameter must to be an integer! %s" % sequence )

        self.sequence = sequence
        self.has_epsilon = False

        if symbols:

            for symbol in symbols:
                self.add( symbol )

        if lock:
            self.lock()

    def __setattr__(self, name, value):
        """
            Block attributes from being changed after it is activated.
            https://stackoverflow.com/questions/17020115/how-to-use-setattr-correctly-avoiding-infinite-recursion
        """

        if self.locked:
            raise AttributeError( "Attributes cannot be changed after `locked` is set to True! %s" % self.__repr__() )

        else:
            super().__setattr__( name, value )

    def __str__(self):
        symbols_str = []

        for symbol in self.symbols:
            symbols_str.append( str( symbol ) )

        return " ".join( symbols_str )

    def __lt__(self, other):

        if isinstance( other, LockableType ):
            return str( self ) < str( other )

        raise TypeError( "'<' not supported between instances of '%s' and '%s'" % (
                self.__class__.__name__, other.__class__.__name__ ) )

    def _len(self):
        lengths = []

        for symbol in self.symbols:
            lengths.append( len( symbol ) )

        return sum( lengths )

    def __getitem__(self, key):
        return self.symbols[key]

    def __iter__(self):
        self.__dict__['index'] = 0
        return self

    def __next__(self):
        index = self.index

        if self.index < len( self.symbols ):
            self.__dict__['index'] += 1
            return self.symbols[index]

        raise StopIteration

    def lock(self):
        """
            Block further changes to this object attributes and save its length for faster access.
        """

        if self.locked:
            return

        self.len = len( self )
        self._len = lambda : self.len

        self.check_consistency()
        super().lock()

    def check_consistency(self):
        """
            Assures the symbol has meaning, i.e., is not empty.
        """

        if not self.symbols:
            raise RuntimeError( "Invalid production creation! Production with no length: `%s` (%s)" % self.symbols, sequence )

    def add(self, symbol):
        """
            Add a new symbol to the production. If the last added symbol and the current are
            Terminal ones, the old terminal is going to be removed and merged into the new one.
        """

        if type( symbol ) not in ( Terminal, NonTerminal ):
            raise RuntimeError( "You can only add Terminal's and NonTerminal's in a Production object! %s" % symbol )

        # Epsilon symbols have length 0
        if len( symbol ) == 0:

            if self.has_epsilon:
                return

            else:
                self.has_epsilon = True

        if not self._merge_terminals( symbol ):
            self.sequence += 1

        symbol.sequence = self.sequence
        symbol.lock()
        self.symbols.append( symbol )

    def _merge_terminals(self, new_symbol):

        if type( new_symbol ) is Terminal:

            if len( self.symbols ):
                last_symbol = self.symbols[-1]

                if type( last_symbol ) is Terminal:
                    new_symbol.str = last_symbol.str + new_symbol.str
                    del self.symbols[-1]
                    return True

        return False

    def _get_symbols(self, symbolType):
        symbols = []

        for symbol in self.symbols:

            if type( symbol ) is symbolType:
                symbols.append( symbol )

        return symbols

    def get_terminals(self):
        """
            Get all Terminal's this symbol is composed by, on their respective sequence/ordering.
        """
        return self._get_symbols( Terminal )

    def get_non_terminals(self):
        """
            Get all NonTerminal's this symbol is composed by, on their respective sequence/ordering.
        """
        return self._get_symbols( NonTerminal )

    @staticmethod
    def is_last_production(symbol, production):
        """
            Checks whether the a given symbol is the last in a production.

            `production` is a list of Terminal's and NonTerminal's, and `symbol` is a NonTerminal.
            The last `production` element has its sequence number equal to the production's list
            size.
        """
        return symbol.sequence >= production[-1].sequence

    @staticmethod
    def copy_productions_except_epsilon(source, destine):
        """
            Copy all productions from one productions set to another, except the epsilon_terminal.

            Return `True` when the item was added in the destine, `False` when is already exists on
            destine.
        """
        is_copied = False

        for production in source:

            if production != epsilon_production:

                if production not in destine:
                    destine.add( production )
                    is_copied = True

        return is_copied


# Standard/common symbols used
epsilon_terminal = Terminal( '&' )
epsilon_production = Production( symbols=[epsilon_terminal], lock=True )


class UpdateGeneretedSentenceThread(QtCore.QThread):
    """
        Dynamically updates the user interface with new sentences generated by the program.
    """
    send_string_signal = QtCore.pyqtSignal( [str] )
    disable_stop_button_signal = QtCore.pyqtSignal()

    def __init__(self, firstGrammar, maximumSentenceSize, isToStop):
        """
            Qt- What is the difference between new QThread(this) and new QThread()?
            https://stackoverflow.com/questions/46293674/qt-what-is-the-difference-between-new-qthreadthis-and-new-qthread
        """
        QtCore.QThread.__init__(self)
        self.isToStop = isToStop

        self.firstGrammar = firstGrammar
        self.maximumSentenceSize = maximumSentenceSize

    def run(self):
        mutex = Lock()
        generate_sentences = []
        only_maximum_sentences = self.only_maximum_sentences

        class ProcessThread(QtCore.QThread):

            def __init__(self, parent, firstGrammar, maximumSentenceSize, isToStop):
                QtCore.QThread.__init__(self, parent)
                self.isToStop = isToStop

                self.firstGrammar = firstGrammar
                self.maximumSentenceSize = maximumSentenceSize

            def run(self):
                nonlocal mutex
                nonlocal generate_sentences
                self.firstGrammar.generate_sentences_of_size_n( self.maximumSentenceSize, generate_sentences, mutex, self.isToStop )

        is_first_time = True
        process_thread = ProcessThread( self.parent(), self.firstGrammar, self.maximumSentenceSize, self.isToStop )
        process_thread.start()
        count = 0

        while process_thread.isRunning() or is_first_time:
            is_first_time = False

            self.sleep( 1 )
            mutex.acquire()

            try:
                sentences_with_length_n = []

                if only_maximum_sentences:

                    for sentence in sorted( generate_sentences ):

                        if len( sentence ) == self.maximumSentenceSize:
                            count += 1
                            sentences_with_length_n.append( "%s. %s" % ( count, sentence ) )

                else:

                    for sentence in sorted( generate_sentences ):
                        count += 1
                        sentences_with_length_n.append( "%s. %s" % ( count, sentence ) )

                if len( sentences_with_length_n ):
                    self.send_string_signal.emit( "\n".join( sentences_with_length_n ) )

                else:
                    self.send_string_signal.emit( "No sentences available yet... "
                            "Current Size %s" % self.firstGrammar.last_non_terminal_length )

                generate_sentences.clear()

            finally:
                mutex.release()

        # If it was not stopped by the close event setting isToStop, then append the success message
        process_thread.wait()

        if not self.isToStop[0]:
            self.send_string_signal.emit( "\nGeneration completed successfully!" )
            self.disable_stop_button_signal.emit()


def trimMessage(message):
    """
        Cuts a message maximum width and length and add an ellipsis (...) when it exceeds 30 lines
        or 150 characters of line size.
    """
    message_lines = message.split( '\n' )
    clean_message = []

    if len( message_lines ) > 30:
        message_lines = message_lines[:30]
        message_lines.append( '\n...' )

    for line in message_lines:

        if len( line ) > 150:
            line = line[:150] + '...'

        clean_message.append( line )

    return "\n".join( clean_message )


def emquote_string(string):
    """
        Return a string escape into single or double quotes accordingly to its contents.
    """
    is_single = "'" in string
    is_double = '"' in string

    if is_single and is_double:
        return '"{}"'.format( string.replace( "'", "\\'" ) )

    if is_single:
        return '"{}"'.format( string )

    return "'{}'".format( string )


def sort_dictionary_lists(dictionary):
    """
        Give a dictionary, call `sorted` on all its elements.
    """

    for key, value in dictionary.items():
        dictionary[key] = sorted( value )

    return dictionary


def ignore_exceptions(function_to_decorate):
    """
        Decorator to catch any exceptions threw and show them to the user on a dialog/message box.
    """

    def wrapper(*args, **kargs):

        try:
            return function_to_decorate( *args, **kargs )

        except Exception as error:
            log.exception( "" )


            msgBox = PyQt5.QtWidgets.QMessageBox( args[0] )
            msgBox.setIcon( PyQt5.QtWidgets.QMessageBox.Information )
            msgBox.setText( "<font size=10 color=green></font>Your operation can not be completed because you entered "
                    "with a invalid language! The program issued the following error message: "
                    "<pre>`<br>%s<br>`</pre>" % trimMessage( str( error ) ) )

            msgBox.addButton( PyQt5.QtWidgets.QMessageBox.Ok )
            msgBox.setDefaultButton( PyQt5.QtWidgets.QMessageBox.No )
            buttonClickResult = msgBox.exec_()

            if buttonClickResult == PyQt5.QtWidgets.QMessageBox.Ok:
                return

    return wrapper


def setTextWithoutCleaningHistory(textWidget, textToSet):
    """
        Making changes to a QTextEdit without adding an undo command to the undo stack
        https://stackoverflow.com/questions/27113262/making-changes-to-a-qtextedit-without-adding-an-undo-command-to-the-undo-stack

        http://doc.qt.io/qt-5/qtextcursor.html#SelectionType-enum
        http://doc.qt.io/qt-5/qtextdocument.html#clearUndoRedoStacks
        http://www.qtcentre.org/threads/43268-Setting-Text-in-QPlainTextEdit-without-Clearing-Undo-Redo-History
    """
    textCursor = textWidget.textCursor()

    # Autoscroll PyQT QTextWidget
    # https://stackoverflow.com/questions/7778726/autoscroll-pyqt-qtextwidget
    verticalScrollBar = textWidget.verticalScrollBar()
    horizontalScrollBar = textWidget.horizontalScrollBar()

    textCursor.beginEditBlock()
    textCursor.select( PyQt5.QtGui.QTextCursor.Document );
    textCursor.removeSelectedText();
    textCursor.insertText( textToSet );
    textCursor.endEditBlock()

    verticalScrollBar.setValue( horizontalScrollBar.maximum() )
    horizontalScrollBar.setValue( horizontalScrollBar.minimum() )


def getCleanSpaces(inputText, minimumLength=0, lineCutTrigger="", keepSpaceSepators=False):
    """
        Removes spaces and comments from the input expression.

        `minimumLength` of a line to not be ignored
        `lineCutTrigger` all lines after a line starting with this string will be ignored
        `keepSpaceSepators` it will keep at a single space between sentences as `S S`, given `S    S`
    """

    if keepSpaceSepators:
        removeNewSpaces = ' '.join( inputText.split( ' ' ) )
        lineCutTriggerNew = ' '.join( lineCutTrigger.split( ' ' ) ).strip( ' ' )

    else:
        removeNewSpaces = re.sub( r"\t| ", "", inputText )
        lineCutTriggerNew = re.sub( r"\t| ", "", lineCutTrigger )

    # log( 1, "%s", inputText, minimumLength=0 )
    lines = removeNewSpaces.split( "\n" )
    clean_lines = []

    for line in lines:

        if keepSpaceSepators:
            line = line.strip( ' ' )

        if minimumLength:

            if len( line ) < minimumLength:
                continue

        if lineCutTrigger:

            if line.startswith( lineCutTriggerNew ):
                break

        if line.startswith( "#" ):
            continue

        clean_lines.append( line )

    return clean_lines


def wrap_text(text, wrap=0, trim_tabs=False, trim_spaces=False, trim_lines=False):
    """
        1. Remove input text leading common indentation, trailing white spaces
        2. If `wrap`, wraps big lists on 80 characters.
        3. If `trim_spaces`, remove leading '+' symbols and if `trim_tabs` replace tabs with 2 spaces.
        4. If `trim_lines`, remove all new line characters.
    """
    clean_lines = []

    if not isinstance( text, str ):
        text = str( text )

    if trim_tabs:
        text = text.replace( '\t', '  ' )

    dedent_lines = textwrap.dedent( text ).strip( '\n' )

    if trim_spaces:

        for line in dedent_lines.split( '\n' ):
            line = line.rstrip( ' ' ).lstrip( '+' )
            clean_lines.append( line )

        dedent_lines = textwrap.dedent( "\n".join( clean_lines ) )

    if wrap:
        clean_lines.clear()

        for line in dedent_lines.split( '\n' ):
            line = textwrap.fill( line, width=wrap )
            clean_lines.append( line )

        dedent_lines = "\n".join( clean_lines )

    if trim_lines:
        dedent_lines = "".join( dedent_lines.split( '\n' ) )

    return dedent_lines

