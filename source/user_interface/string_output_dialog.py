#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# Licensing
#
# String Output Dialog
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
import PyQt5

from PyQt5.QtGui import QKeySequence

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QCoreApplication

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QFileDialog

from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout

from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QShortcut


from debug_tools import getLogger

# Enable debug messages: ( bitwise )
log = getLogger( 127, __name__ )
log( 1, "Importing " + __name__ )

from debug_tools.utilities import wrap_text

from .utilities import get_screen_center
from .utilities import ignore_exceptions
from .utilities import set_scroll_to_maximum
from .utilities import setTextWithoutCleaningHistory


class StringOutputDialog(QMainWindow):
    """
        How can I show a PyQt modal dialog and get data out of its controls once its closed?
        https://stackoverflow.com/questions/18196799/how-can-i-show-a-pyqt-modal-dialog-and-get-data-out-of-its-controls-once-its-clo

        how to clear child window reference stored in parent application when child window is closed?
        https://stackoverflow.com/questions/27420338/how-to-clear-child-window-reference-stored-in-parent-application-when-child-wind
    """

    def __init__(self, parent, settings, fontOptions, fileDialogOptions, isToStop):
        super().__init__( parent )
        self.settings = settings
        self.isToStop = isToStop
        self.fileDialogOptions = fileDialogOptions

        # QWidget::setLayout: Attempting to set QLayout “” on ProgramWindow “”, which already has a layout
        # https://stackoverflow.com/questions/50176661/qwidgetsetlayout-attempting-to-set-qlayout-on-programwindow-which-alre
        self.centralwidget = QWidget()
        self.setCentralWidget( self.centralwidget )
        self.setWindowTitle( "Results output window" )

        # Initial window size/pos last saved. Use default values for first time
        windowScreenGeometry = self.settings.value( "stringOutputWindowScreenGeometry" )
        windowScreenState = self.settings.value( "stringOutputWindowScreenState" )

        if windowScreenGeometry:
            self.restoreGeometry( windowScreenGeometry )

        else:
            self.resize( 600, 400 )
            # self.move( get_screen_center( self ) )

        if windowScreenState:
            self.restoreState( windowScreenState )

        # nice widget for editing the date
        self.textEditWidget = QPlainTextEdit( self )

        # Detect Ctrl+S ion QTextedit?
        # https://stackoverflow.com/questions/43010630/detect-ctrls-ion-qtextedit
        enterShortcut = QShortcut( QKeySequence( "Ctrl+Enter" ), self.textEditWidget )
        returnShortcut = QShortcut( QKeySequence( "Ctrl+Return" ), self.textEditWidget )
        enterShortcut.activated.connect( self.close )
        returnShortcut.activated.connect( self.close )

        # Change font, colour of text entry box
        self.textEditWidget.setStyleSheet( fontOptions )

        # Set initial value of text
        self.textEditWidget.document().setPlainText( "" )
        self.textEditWidget.setLineWrapMode( QPlainTextEdit.NoWrap )

        # OK and Cancel buttons
        self.standardButtons = QDialogButtonBox( QDialogButtonBox.Ok | QDialogButtonBox.Abort, Qt.Horizontal, self )
        self.saveFileButton = QPushButton( "Save results to a file" )

        self.okButton = self.standardButtons.button( QDialogButtonBox.Ok )
        self.okButton.setText( 'Close' )

        self.stopButton = self.standardButtons.button( QDialogButtonBox.Abort )
        self.stopButton.setText( 'Stop Processing' )

        self.standardButtons.accepted.connect( self.close )
        self.standardButtons.rejected.connect( self.stopProcessing )
        self.saveFileButton.clicked.connect( self.handleSaveFileCall )

        # Setup the main layout
        self.verticalLayout = QVBoxLayout( self.centralwidget )
        self.horizontalLayout = QHBoxLayout()

        self.verticalLayout.addWidget( self.textEditWidget )
        self.verticalLayout.addLayout( self.horizontalLayout )

        self.horizontalLayout.addWidget( self.saveFileButton )
        self.horizontalLayout.addWidget( self.standardButtons )

    def appendText(self, textToAppend):
        self.textEditWidget.appendPlainText( textToAppend )
        self.textEditWidget.repaint()
        QCoreApplication.processEvents()

    def saveCursorPosition(self):
        textEditWidget = self.textEditWidget
        self.textCursor = textEditWidget.textCursor()
        self.cursorPosition = self.textCursor.position()

    def restoreCursorPosition(self):
        textCursor = self.textCursor
        textEditWidget = self.textEditWidget
        textCursor.setPosition( self.cursorPosition )
        textEditWidget.setTextCursor( textCursor )
        set_scroll_to_maximum( textEditWidget )

    def setScrollToMaximum(self):
        textEditWidget = self.textEditWidget
        set_scroll_to_maximum( textEditWidget, True )

    def disableStopButton(self):
        self.stopButton.setEnabled( False )

    def stopProcessing(self):
        self.isToStop[0] = True
        self.disableStopButton()

    def closeEvent(self, event=None):
        # log( 1, "closeEvent" )
        self.settings.setValue( "stringOutputWindowScreenGeometry", self.saveGeometry() )
        self.settings.setValue( "stringOutputWindowScreenState", self.saveState() )

        # super().closeEvent( event )
        # self.event.quit()

        self.stopProcessing()
        self.deleteLater()

    def keyPressEvent(self, event):
        """
            Closes the application when the escape key is pressed.
        """

        if event.key() == PyQt5.QtCore.Qt.Key_Escape:
            self.close()

    @ignore_exceptions
    def handleSaveFileCall(self, qt_decorator_bug):
        fileName, _ = QFileDialog.getSaveFileName( self, "Choose a name", "","Text Files (*.txt)", options=self.fileDialogOptions )

        if fileName:

            with open( fileName + '.txt', 'w', encoding='utf-8' ) as file:
                file.write( self.textEditWidget.toPlainText() )

