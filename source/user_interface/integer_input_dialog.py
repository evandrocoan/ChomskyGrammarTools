#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# Licensing
#
# Integer Input Dialog
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

from PyQt5.QtGui import QKeySequence

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QEventLoop

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QWidget

from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QShortcut

from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtWidgets import QPushButton

from debug_tools import getLogger

# Enable debug messages: ( bitwise )
log = getLogger( 127, __name__ )
log( 1, "Importing " + __name__ )

from debug_tools.utilities import wrap_text
from debug_tools.utilities import getCleanSpaces

from .utilities import get_screen_center
from .utilities import ignore_exceptions
from .utilities import setTextWithoutCleaningHistory


class IntegerInputDialog(QMainWindow):
    """
        How can I show a PyQt modal dialog and get data out of its controls once its closed?
        https://stackoverflow.com/questions/18196799/how-can-i-show-a-pyqt-modal-dialog-and-get-data-out-of-its-controls-once-its-clo

        how to clear child window reference stored in parent application when child window is closed?
        https://stackoverflow.com/questions/27420338/how-to-clear-child-window-reference-stored-in-parent-application-when-child-wind
    """

    def __init__(self, parent, settings, fontOptions):
        super().__init__( parent )
        self.result = 0

        self.settings = settings
        self.setAttribute( Qt.WA_DeleteOnClose )

        # QWidget::setLayout: Attempting to set QLayout “” on ProgramWindow “”, which already has a layout
        # https://stackoverflow.com/questions/50176661/qwidgetsetlayout-attempting-to-set-qlayout-on-programwindow-which-alre
        self.centralwidget = QWidget()
        self.setCentralWidget( self.centralwidget )
        self.setWindowTitle( "Input a Integer value" )

        # Initial window size/pos last saved. Use default values for first time
        windowScreenGeometry = self.settings.value( "integerInputWindowScreenGeometry" )
        windowScreenState = self.settings.value( "integerInputWindowScreenState" )

        if windowScreenGeometry:
            self.restoreGeometry( windowScreenGeometry )

        else:
            self.resize( 600, 400 )
            # self.move( get_screen_center( self ) )

        if windowScreenState:
            self.restoreState( windowScreenState )

        # nice widget for editing the date
        self.textEditWidget = QPlainTextEdit( self )
        self.textEditWidget.setLineWrapMode( QPlainTextEdit.NoWrap )

        # Detect Ctrl+S ion QTextedit?
        # https://stackoverflow.com/questions/43010630/detect-ctrls-ion-qtextedit
        enterShortcut = QShortcut( QKeySequence( "Ctrl+Enter" ), self.textEditWidget )
        returnShortcut = QShortcut( QKeySequence( "Ctrl+Return" ), self.textEditWidget )
        enterShortcut.activated.connect( self.accept )
        returnShortcut.activated.connect( self.accept )

        # Change font, colour of text entry box
        self.textEditWidget.setStyleSheet( fontOptions )
        self.textEditWidget.installEventFilter( self )

        # Set initial value of text
        self.textEditWidget.document().setPlainText( "# Write here bellow, an integer with the number of steps\n\n5" )
        self.textEditWidget.selectAll()

        # OK and Cancel buttons
        self.standardButtons = QDialogButtonBox( QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self )
        self.standardButtons.accepted.connect( self.accept )
        self.standardButtons.rejected.connect( self.reject )

        # Setup the main layout
        self.verticalLayout = QVBoxLayout( self.centralwidget )
        self.horizontalLayout = QHBoxLayout()

        self.verticalLayout.addWidget( self.textEditWidget )
        self.verticalLayout.addLayout( self.horizontalLayout )

        self.horizontalLayout.addWidget( self.standardButtons )

    def accept(self):
        # log( 1, "Print done" )
        self.result = QDialog.Accepted
        self.close()

    def reject(self):
        # log( 1, "Print reject" )
        self.result = QDialog.Rejected
        self.close()

    def exec_(self):
        """
            Problems with connect in pyqt5
            https://stackoverflow.com/questions/33236358/problems-with-connect-in-pyqt5
        """
        # log( 1, "Blocking main ui" )
        self.event = QEventLoop()
        self.setWindowModality( Qt.ApplicationModal )

        self.show()
        self.event.exec()
        return self.result

    def closeEvent(self, event=None):
        # log( 1, "closeEvent " )
        self.settings.setValue( "integerInputWindowScreenGeometry", self.saveGeometry() )
        self.settings.setValue( "integerInputWindowScreenState", self.saveState() )

        # super().closeEvent( event )
        self.event.quit()

    def keyPressEvent(self, event):
        """
            Closes the application when the escape key is pressed.
        """
        # log( 1, "Key pressing: %s", event.key() )

        if event.key() == PyQt5.QtCore.Qt.Key_Escape:
            self.close()

    def eventFilter(self, obj, event):
        """
            eventFilter on a QWidget with PyQt4
            https://stackoverflow.com/questions/28050397/eventfilter-on-a-qwidget-with-pyqt4
        """

        if event.type() == PyQt5.QtCore.QEvent.KeyPress:
            key = event.key()
            # log( 1, "Key pressing: %s", event.key() )

            if key == Qt.Key_Return or key == Qt.Key_Enter:
                self.clearTextSelection()
                self.accept()

        return super().eventFilter( obj, event )

    def clearTextSelection(self):
        textCursor = self.textEditWidget.textCursor()
        textCursor.clearSelection()
        self.textEditWidget.setTextCursor( textCursor )

    # static method to create the dialog and return ( date, time, accepted )
    @classmethod
    def getNewUserInput(cls, parent, settings, fontOptions):
        result = 1
        integer = 5

        while result:
            dialog = IntegerInputDialog( parent, settings, fontOptions )
            result = dialog.exec_()

            if result:
                # log( 1, "dialog.textEditWidget.toPlainText(): %s", dialog.textEditWidget.toPlainText() )
                integer = cls.convertToInteger( parent, dialog.textEditWidget.toPlainText() )

                if integer is not None:
                    break

            else:
                break

        # log( 1, "result: %s, integer: %s", result, integer )
        return ( integer, result == QDialog.Accepted )

    @staticmethod
    @ignore_exceptions
    def convertToInteger(parent, inputString):
        # log( 1, "inputString: %s", inputString )
        inputString = "".join( getCleanSpaces( inputString ) )
        inputInteger = int( inputString )

        if inputInteger < 0:
            raise RuntimeError( "You cannot enter negative values!" )

        return inputInteger
