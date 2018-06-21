#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import PyQt5

# from PyQt5.QtGui import *
# from PyQt5.QtCore import *
# from PyQt5.QtWidgets import *

from user_interface.string_input_dialog import InputStringDialog
from user_interface.string_output_dialog import StringOutputDialog
from user_interface.integer_input_dialog import InputIntegerDialog

from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QFileDialog

from grammar.grammar import ChomskyGrammar
from grammar.symbols import HISTORY_KEY_LINE

from grammar.run_function_async import run_function_async

from grammar.utilities import wrap_text
from grammar.utilities import ignore_exceptions
from grammar.utilities import setTextWithoutCleaningHistory
from grammar.utilities import trimMessage
from grammar.utilities import getCleanSpaces
from grammar.utilities import dictionary_to_string

from debug_tools import getLogger

# Enable debug messages: ( bitwise )
# 0   - Disabled debugging
# 1   - Basic logging messages
# 32  - Boxes geometries
# 127 - All debugging levels at the same time.
log = getLogger( 127-32, os.path.basename( os.path.dirname( os.path.abspath ( __file__ ) ) ) )
log( 1, "Importing " + __name__ )


def main():
    app = QtWidgets.QApplication( sys.argv )
    programWindow = ProgramWindow()

    log( 1, "Opening main window..." )
    programWindow.show()
    exit_code = app.exec_()

    log( 1, "Closing main window..." )
    log( 1, "exit_code: %s", exit_code )
    sys.exit( exit_code )


class ProgramWindow(QtWidgets.QMainWindow):

    send_string_signal = QtCore.pyqtSignal( [str] )

    def show_error_message_box(self, error_message):
        parent = self
        msgBox = PyQt5.QtWidgets.QMessageBox( parent )

        msgBox.setIcon( PyQt5.QtWidgets.QMessageBox.Information )
        msgBox.setText( "<font size=10 color=green></font>Your operation can not be completed because you entered "
                "with a invalid language! The program issued the following error message: "
                "<pre>`<br>%s<br>`</pre>" % trimMessage( error_message ) )

        msgBox.addButton( PyQt5.QtWidgets.QMessageBox.Ok )
        msgBox.setDefaultButton( PyQt5.QtWidgets.QMessageBox.No )
        buttonClickResult = msgBox.exec_()

        if buttonClickResult == PyQt5.QtWidgets.QMessageBox.Ok:
            return

    def setup_main_excpetion_handler(self):
        """
            PyQt4.QtCore.pyqtSignal object has no attribute 'connect'
            https://stackoverflow.com/questions/2970312/pyqt4-qtcore-pyqtsignal-object-has-no-attribute-connect

            Python decorators in classes
            https://stackoverflow.com/questions/1263451/python-decorators-in-classes

            Updating GUI elements in MultiThreaded PyQT
            https://stackoverflow.com/questions/9957195/updating-gui-elements-in-multithreaded-pyqt
        """
        self.send_string_signal.connect( self.show_error_message_box )
        ignore_exceptions.send_string_signal = self.send_string_signal

    def __init__(self):
        QtWidgets.QMainWindow.__init__( self )
        self.setup_main_window()
        self.setup_main_excpetion_handler()

        # self.verticalSpacer = QtWidgets.QSpacerItem( 0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding )
        self.create_grammar_input_text()
        self.set_window_layout()

    def setup_main_window(self):
        self.largestFirstCollumn = 0

        self.resize( 800, 600  )
        self.setWindowTitle( "Trabalho 2 de Formais - Evandro Coan" )

        # https://github.com/GNOME/adwaita-icon-theme
        # https://code.google.com/archive/p/faenza-icon-theme/
        self.mainApplicationIcon = QtGui.QIcon( "../login.png" )

        # PyQt4 set windows taskbar icon
        # https://stackoverflow.com/questions/12432637/pyqt4-set-windows-taskbar-icon
        # https://stackoverflow.com/questions/44161669/how-to-set-a-python-qt4-window-icon
        self.setWindowIcon( self.mainApplicationIcon )

        # QWidget::setLayout: Attempting to set QLayout “” on ProgramWindow “”, which already has a layout
        # https://stackoverflow.com/questions/50176661/qwidgetsetlayout-attempting-to-set-qlayout-on-programwindow-which-alre
        self.centralwidget = QWidget()
        self.setCentralWidget( self.centralwidget )

    def create_grammar_input_text(self):
        # https://www.penwatch.net/cms/pyqt5_qplaintextedit/
        self.grammarTextEditWidget = QPlainTextEdit( self )
        self.grammarTextEditWidget.setLineWrapMode( QPlainTextEdit.NoWrap )

        # Change font, colour of text entry box
        self.grammarTextEditWidget.setStyleSheet( self.getMainFontOptions() )

        # Set initial value of text
        self.grammarTextEditWidget.document().setPlainText( wrap_text( """
            # Write your Grammar here
            S -> a A | a
            A -> b S | b
        """ ) )

        self.redoGrammarButton        = QPushButton( "Redo Operations" )
        self.undoGrammarButton        = QPushButton( "Undo Operations" )
        self.isGrammarEmpty           = QPushButton( "Is Empty" )
        self.isGrammarFinite          = QPushButton( "Is Finite" )
        self.isGrammarInfinite        = QPushButton( "Is Infinite" )
        self.isGrammarEmptyOrInFinite = QPushButton( "Is Empty Or (In)Finite" )
        self.calculateFirstAndFollow  = QPushButton( "Compute First and Follow" )
        self.openGrammar              = QPushButton( "Open File" )
        self.saveGrammar              = QPushButton( "Save File" )
        self.grammarBeautifing        = QPushButton( "Beautify" )

        self.undoGrammarButton.clicked.connect( self.handleUndoGrammarTextEdit )
        self.redoGrammarButton.clicked.connect( self.handleRedoGrammarTextEdit )
        self.calculateFirstAndFollow.clicked.connect( self.handleCalculateFirstAndFollow )
        self.isGrammarEmptyOrInFinite.clicked.connect( self.handleGrammarIsFiniteInfiniteOrEmpty )
        self.isGrammarEmpty.clicked.connect( self.handleIsGrammarEmpty )
        self.isGrammarFinite.clicked.connect( self.handleIsGrammarFinite )
        self.isGrammarInfinite.clicked.connect( self.handleIsGrammarInfinite )
        self.openGrammar.clicked.connect( self.handleOpenGrammar )
        self.saveGrammar.clicked.connect( self.handleSaveGrammar )
        self.grammarBeautifing.clicked.connect( self.handleGrammarBeautifing)

        # The distances between the QPushButton in QGridLayout
        # https://stackoverflow.com/questions/13578187/the-distances-between-the-qpushbutton-in-qgridlayout
        self.grammarVerticalGridLayout = QGridLayout()
        self.grammarVerticalGridLayout.addWidget( self.undoGrammarButton,        0,  0)
        self.grammarVerticalGridLayout.addWidget( self.redoGrammarButton,        1,  0)
        self.grammarVerticalGridLayout.addWidget( self.get_vertical_separator(), 2,  0)
        self.grammarVerticalGridLayout.addWidget( self.calculateFirstAndFollow,  3,  0)
        self.grammarVerticalGridLayout.addWidget( self.isGrammarEmptyOrInFinite, 4,  0)
        self.grammarVerticalGridLayout.addWidget( self.isGrammarEmpty,           5,  0)
        self.grammarVerticalGridLayout.addWidget( self.isGrammarFinite,          6,  0)
        self.grammarVerticalGridLayout.addWidget( self.isGrammarInfinite,        7,  0)
        self.grammarVerticalGridLayout.addWidget( self.get_vertical_separator(), 8,  0)
        self.grammarVerticalGridLayout.addWidget( self.openGrammar,              9,  0)
        self.grammarVerticalGridLayout.addWidget( self.saveGrammar,              10, 0)
        self.grammarVerticalGridLayout.addWidget( self.grammarBeautifing,        11, 0)
        self.grammarVerticalGridLayout.setSpacing( 0 )
        self.grammarVerticalGridLayout.setAlignment(Qt.AlignTop)

        # How to align the layouts QHBoxLayout and QVBoxLayout on pyqt4?
        # https://stackoverflow.com/questions/44230856/how-to-align-the-layouts-qhboxlayout-and-qvboxlayout-on-pyqt4
        self.grammarInnerLayout = QHBoxLayout()
        self.grammarInnerLayout.addLayout( self.grammarVerticalGridLayout )
        self.grammarInnerLayout.addWidget( self.grammarTextEditWidget )

    def get_vertical_separator(self):
        """
            http://www.qtcentre.org/threads/24433-Separator-in-box-layout
            https://stackoverflow.com/questions/10082299/qvboxlayout-how-to-vertically-align-widgets-to-the-top-instead-of-the-center

            How to increase QFrame.HLine line separator width and distance with the other buttons?
            https://stackoverflow.com/questions/50825126/how-to-increase-qframe-hline-line-separator-width-and-distance-with-the-other-bu
        """
        separator_line = QFrame()
        separator_line.setFrameShape( QFrame.HLine )
        separator_line.setFrameShadow( QFrame.Plain )

        sizePolicy = QtWidgets.QSizePolicy( QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred )
        sizePolicy.setHeightForWidth( separator_line.sizePolicy().hasHeightForWidth() )
        separator_line.setSizePolicy( sizePolicy )
        separator_line.setStyleSheet( "font: 9pt; color: #000088;" )
        separator_line.setLineWidth( 2.5 )
        separator_line.setMidLineWidth( 10 )
        separator_line.setMinimumSize( 3, 10 )
        return separator_line

    def set_window_layout(self):
        # Creates a box to align vertically the panels
        # https://doc.qt.io/qt-4.8/qvboxlayout.html
        #
        # Review example
        # http://zetcode.com/gui/pyqt4/layoutmanagement/
        #
        # QWidget::setLayout: Attempting to set QLayout “” on ProgramWindow “”, which already has a layout
        # https://stackoverflow.com/questions/50176661/qwidgetsetlayout-attempting-to-set-qlayout-on-programwindow-which-alre
        main_vertical_layout = QVBoxLayout( self.centralwidget )
        main_vertical_layout.addLayout( self.grammarInnerLayout )

    def keyPressEvent(self, event):
        """
            Closes the application when the escape key is pressed.
        """

        if event.key() == PyQt5.QtCore.Qt.Key_Escape:
            self.close()

    def handleUndoGrammarTextEdit(self):
        self.grammarTextEditWidget.document().undo()

    def handleRedoGrammarTextEdit(self):
        self.grammarTextEditWidget.document().redo()

    def _getFileDialogOptions(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        return options

    def getMainFontOptions(self):
        """
            Qt Style Sheets Reference
            http://doc.qt.io/archives/qt-4.8/stylesheet-reference.html
        """
        return """QPlainTextEdit
            {
                background-color: #333;
                color: #00FF00;
                font-size: 16px;
                font-family: Consolas, Monospace, Menlo Regular, Inconsolata, Menlo, Courier;
            }
        """

    @ignore_exceptions
    def handleSaveGrammar(self):
        options = self._getFileDialogOptions()
        fileName, _ = QFileDialog.getSaveFileName( self, "Choose a name for your grammar", "","Grammar Files (*.grammar)", options=options )

        if fileName:

            with open( fileName + '.grammar', 'w', encoding='utf-8' ) as file:
                file.write( self.grammarTextEditWidget.toPlainText() )

    @ignore_exceptions
    def handleOpenGrammar(self):
        inputGrammar = self._openGrammar()
        setTextWithoutCleaningHistory( self.grammarTextEditWidget, inputGrammar )

    @ignore_exceptions
    def _openGrammar(self):
        options = self._getFileDialogOptions()
        fileName, _ = QFileDialog.getOpenFileName( self, "Choose a grammar", "","Grammar Files (*.grammar)", options=options )

        if fileName:

            with open( fileName, 'r', encoding='utf-8' ) as file:
                return file.read()

    @ignore_exceptions
    def handleGrammarBeautifing(self, qt_decorator_bug):
        firstGrammar = ChomskyGrammar.load_from_text_lines( self.grammarTextEditWidget.toPlainText() )
        firstGrammar.beautify( 0 )

        # log( 1, "firstGrammar: %s", firstGrammar )
        setTextWithoutCleaningHistory( self.grammarTextEditWidget, str( firstGrammar ) )

    @ignore_exceptions
    def _handleFunctionAsync(self, target_function, initial_message):
        isToStop = [False]

        results_dialog = StringOutputDialog( self, self.getMainFontOptions(), self._getFileDialogOptions(), isToStop )
        results_dialog.appendText( initial_message + '\n' )

        target_function.results = ""
        target_function.isToStop = isToStop
        run_function_async( target_function, results_dialog )

    @ignore_exceptions
    def handleCalculateFirstAndFollow(self, qt_decorator_bug):

        @ignore_exceptions
        def function():
            results = []
            firstGrammar = ChomskyGrammar.load_from_text_lines( self.grammarTextEditWidget.toPlainText() )
            first_terminals = firstGrammar.first_terminals()
            first_non_terminals = firstGrammar.first_non_terminals()
            follow_terminals = firstGrammar.follow_terminals( first_terminals )

            results.append( "Terminal's FIRST\n" )
            results.append( dictionary_to_string( first_terminals ) )
            results.append( "\n\nNon Terminal's FIRST\n" )
            results.append( dictionary_to_string( first_non_terminals ) )
            results.append( "\n\nTerminal's FOLLOW\n" )
            results.append( dictionary_to_string( follow_terminals ) )
            results.append( "\n\nComputation completed successfully!" )
            function.results = "".join( results )

        self._handleFunctionAsync( function, "The computed FIRST and FOLLOW for the given grammar are:" )

    @ignore_exceptions
    def _handleGrammarIsSomething(self, function_to_check, property_name):
        """
            How to pass member function as argument in python?
            https://stackoverflow.com/questions/10181450/how-to-pass-member-function-as-argument-in-python
        """

        @ignore_exceptions
        def function():
            results = []
            firstGrammar = ChomskyGrammar.load_from_text_lines( self.grammarTextEditWidget.toPlainText() )
            is_empty = function_to_check( firstGrammar )

            results.append( str( firstGrammar ) )
            results.append( "\n\nIs %s%s.\n" % ( "" if is_empty else "NOT ", property_name ) )
            function.results = "".join( results )

        self._handleFunctionAsync( function, "The following grammar:" )

    @ignore_exceptions
    def handleGrammarIsFiniteInfiniteOrEmpty(self, qt_decorator_bug):

        @ignore_exceptions
        def function():
            results = []
            firstGrammar = ChomskyGrammar.load_from_text_lines( self.grammarTextEditWidget.toPlainText() )
            is_empty = firstGrammar.is_empty()
            is_finite = firstGrammar.is_finite()
            is_infinite = firstGrammar.is_infinite()

            if is_empty:
                property_name = "Empty"

            elif is_finite:
                property_name = "Finite"

            elif is_infinite:
                property_name = "Infinite"

            else:
                property_name = "Unknown"

            results.append( str( firstGrammar ) )
            results.append( "\n\nIs %s.\n" % ( property_name ) )
            function.results = "".join( results )

        self._handleFunctionAsync( function, "The following grammar:" )

    @ignore_exceptions
    def handleIsGrammarEmpty(self, function_to_check):
        self._handleGrammarIsSomething( ChomskyGrammar.is_empty, "empty" )

    @ignore_exceptions
    def handleIsGrammarFinite(self, function_to_check):
        self._handleGrammarIsSomething( ChomskyGrammar.is_finite, "finite" )

    @ignore_exceptions
    def handleIsGrammarInfinite(self, function_to_check):
        self._handleGrammarIsSomething( ChomskyGrammar.is_infinite, "infinite" )


if __name__ == "__main__":
    main()

