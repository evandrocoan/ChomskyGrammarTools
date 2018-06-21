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

    programWindow.show()
    sys.exit( app.exec_() )


class ProgramWindow(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__( self )
        self.setup_main_window()

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
        self.grammarTextEditWidget.setStyleSheet( self._getMainFontOptions() )

        # Set initial value of text
        self.grammarTextEditWidget.document().setPlainText( wrap_text( """
            # Write your Grammar here
            S -> a A | a
            A -> b S | b
        """ ) )

        # http://www.qtcentre.org/threads/24433-Separator-in-box-layout
        # https://stackoverflow.com/questions/10082299/qvboxlayout-how-to-vertically-align-widgets-to-the-top-instead-of-the-center
        self.separatorLine = QFrame()
        self.separatorLine.setFrameShape( QFrame.HLine )
        self.separatorLine.setFrameShadow( QFrame.Plain )

        self.redoGrammarButton        = QPushButton( "Redo Operations" )
        self.undoGrammarButton        = QPushButton( "Undo Operations" )
        self.calculateFirstAndFollow  = QPushButton( "Compute First and Follow" )
        self.openGrammar              = QPushButton( "Open File" )
        self.saveGrammar              = QPushButton( "Save File" )
        self.grammarBeautifing        = QPushButton( "Beautify" )

        self.undoGrammarButton.clicked.connect( self.handleUndoGrammarTextEdit )
        self.redoGrammarButton.clicked.connect( self.handleRedoGrammarTextEdit )
        self.calculateFirstAndFollow.clicked.connect( self.handleCalculateFirstAndFollow )
        self.openGrammar.clicked.connect( self.handleOpenGrammar )
        self.saveGrammar.clicked.connect( self.handleSaveGrammar )
        self.grammarBeautifing.clicked.connect( self.handleGrammarBeautifing)

        # The distances between the QPushButton in QGridLayout
        # https://stackoverflow.com/questions/13578187/the-distances-between-the-qpushbutton-in-qgridlayout
        self.grammarVerticalGridLayout = QGridLayout()
        self.grammarVerticalGridLayout.addWidget( self.undoGrammarButton,       0, 0)
        self.grammarVerticalGridLayout.addWidget( self.redoGrammarButton,       1, 0)
        self.grammarVerticalGridLayout.addWidget( self.calculateFirstAndFollow, 2, 0)
        self.grammarVerticalGridLayout.addWidget( self.separatorLine,           3, 0)
        self.grammarVerticalGridLayout.addWidget( self.openGrammar,             4, 0)
        self.grammarVerticalGridLayout.addWidget( self.saveGrammar,             5, 0)
        self.grammarVerticalGridLayout.addWidget( self.grammarBeautifing,       6, 0)
        self.grammarVerticalGridLayout.setSpacing( 0 )
        self.grammarVerticalGridLayout.setAlignment(Qt.AlignTop)

        # How to align the layouts QHBoxLayout and QVBoxLayout on pyqt4?
        # https://stackoverflow.com/questions/44230856/how-to-align-the-layouts-qhboxlayout-and-qvboxlayout-on-pyqt4
        self.grammarInnerLayout = QHBoxLayout()
        self.grammarInnerLayout.addLayout( self.grammarVerticalGridLayout )
        self.grammarInnerLayout.addWidget( self.grammarTextEditWidget )

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

    def _getMainFontOptions(self):
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
    def handleCalculateFirstAndFollow(self, qt_decorator_bug):
        isToStop = [False]

        results_dialog = StringOutputDialog( self, self._getMainFontOptions(), self._getFileDialogOptions(), isToStop )
        results_dialog.appendText( wrap_text( """
            The computed FIRST and FOLLOW for the given grammar are:
        """ ) + '\n' )

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

        function.results = ""
        function.isToStop = isToStop
        run_function_async( function, results_dialog )


if __name__ == "__main__":
    main()

