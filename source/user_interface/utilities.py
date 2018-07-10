#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# Licensing
#
# Project Utilities
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

import PyQt5
import textwrap

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QCoreApplication

from debug_tools import getLogger
log = getLogger( 127, __name__ )


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
            ignore_exceptions.send_string_signal.emit( str( error ) )

    return wrapper


def set_scroll_to_maximum(textEditWidget, to_bottom=False):
    """
        Given a text edit area, set its scrolling completely to the bottom.
    """

    # Autoscroll PyQT QTextWidget
    # https://stackoverflow.com/questions/7778726/autoscroll-pyqt-qtextwidget
    verticalScrollBar = textEditWidget.verticalScrollBar()
    horizontalScrollBar = textEditWidget.horizontalScrollBar()

    if to_bottom:
        textEditWidget.moveCursor( QtGui.QTextCursor.End )
        verticalScrollBar.setValue( verticalScrollBar.maximum() )
        horizontalScrollBar.setValue( horizontalScrollBar.minimum() )

    textEditWidget.moveCursor( QtGui.QTextCursor.StartOfLine )
    textEditWidget.ensureCursorVisible()

    textEditWidget.repaint()
    QCoreApplication.processEvents()


def get_screen_center(self):
    """
        PyQt4 what is the best way to center dialog windows?
        https://stackoverflow.com/questions/12432740/pyqt4-what-is-the-best-way-to-center-dialog-windows
    """
    screenGeometry = QtWidgets.QApplication.desktop().screenGeometry()
    x = ( screenGeometry.width() - self.width() ) / 2
    y = ( screenGeometry.height() - self.height() ) / 2
    return QPoint( x, y )


def setTextWithoutCleaningHistory(textEditWidget, textToSet):
    """
        Making changes to a QTextEdit without adding an undo command to the undo stack
        https://stackoverflow.com/questions/27113262/making-changes-to-a-qtextedit-without-adding-an-undo-command-to-the-undo-stack

        http://doc.qt.io/qt-5/qtextcursor.html#SelectionType-enum
        http://doc.qt.io/qt-5/qtextdocument.html#clearUndoRedoStacks
        http://www.qtcentre.org/threads/43268-Setting-Text-in-QPlainTextEdit-without-Clearing-Undo-Redo-History
    """
    textCursor = textEditWidget.textCursor()
    position = textCursor.position()

    textCursor.beginEditBlock()
    textCursor.select( PyQt5.QtGui.QTextCursor.Document );
    textCursor.removeSelectedText();
    textCursor.insertText( textToSet );
    textCursor.endEditBlock()

    # textCursor.setPosition( position );
    # textEditWidget.setTextCursor( textCursor )

    # PyQT force update textEdit before calling other function
    # https://stackoverflow.com/questions/47654327/pyqt-force-update-textedit-before-calling-other-function
    textEditWidget.repaint()
    QCoreApplication.processEvents()

