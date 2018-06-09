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
log = getLogger( 127, os.path.basename( os.path.dirname( os.path.abspath ( __file__ ) ) ) )

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
class ChomskyGrammarTreeTransformer( lark.Transformer ):
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
        return str( non_terminal[0] )

    def terminal(self, _terminal):
        return str( _terminal[0] )

    def epsilon(self, _terminal):
        return self._parse_symbol( _terminal, '&' )

    def quote(self, _terminal):
        return self._parse_symbol( _terminal, "'" )

    def dash_phi_hyphen(self, _terminal):
        return self._parse_symbol( _terminal, "-" )

    def _parse_symbol(self, _terminal, default):

        if len( _terminal ):
            return str( _terminal[0] )

        return default

    def non_terminal(self, _non_terminals):
        results = []
        # log( 1, 'productions: %s', _non_terminals )

        for _non_terminal in _non_terminals:
            results.append( str( _non_terminal[0] ) )

        return "".join( results )

    def production(self, productions):
        # log( 1, 'productions: %s', productions )

        if len( productions ) > 1:
            return ( str( productions[0] ), str( productions[1] ) )

        return ( str( productions[0] ), '' )


class UpdateGeneretedSentenceThread(QtCore.QThread):

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


def getCleanSpaces(inputText, minimiumLength=0, lineCutTrigger=""):
    """
        Removes spaces and comments from the input expression.
    """
    removeNewSpaces = re.sub( r"\t| ", "", inputText )
    lineCutTriggerNew = re.sub( r"\t| ", "", lineCutTrigger )

    # log( 1, "%s", inputText, minimiumLength=0 )
    lines = removeNewSpaces.split( "\n" )
    clean_lines = []

    for line in lines:

        if minimiumLength:

            if len( line ) < minimiumLength:
                continue

        if lineCutTrigger:

            if line.startswith( lineCutTriggerNew ):
                break

        if line.startswith( "#" ):
            continue

        clean_lines.append( line )

    return clean_lines


def wrap_text(text, wrap_at_80=False, trim_tabs=False, trim_spaces=False):
    """
        1. Remove input text leading common indentation, trailing white spaces
        2. Remove leading '+' symbols and replace tabs with 2 spaces.
        3. Wraps big lists on 80 characters.
    """
    clean_lines = []

    if trim_tabs:
        text = text.replace( '\t', '  ' )

    dedent_lines = textwrap.dedent( text ).strip( '\n' )

    if trim_spaces:

        for line in dedent_lines.split( '\n' ):
            line = line.rstrip( ' ' ).lstrip( '+' )
            clean_lines.append( line )

        dedent_lines = textwrap.dedent( "\n".join( clean_lines ) )

    if wrap_at_80:
        clean_lines.clear()

        for line in dedent_lines.split( '\n' ):
            line = textwrap.fill( line, width=80 )
            clean_lines.append( line )

        dedent_lines = "\n".join( clean_lines )

    return dedent_lines

