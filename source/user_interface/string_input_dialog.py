#! /usr/bin/env python
# -*- coding: utf-8 -*-

import PyQt5

from PyQt5.QtGui import QKeySequence

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QDateTime
from PyQt5.QtCore import QEventLoop

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QDateTimeEdit
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QShortcut

from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout

from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtWidgets import QPushButton

from debug_tools import getLogger

# Enable debug messages: ( bitwise )
log = getLogger( 127, __name__ )
log( 1, "Importing " + __name__ )

from grammar.utilities import wrap_text
from grammar.utilities import ignore_exceptions
from grammar.utilities import setTextWithoutCleaningHistory


class StringInputDialog(QMainWindow):
    """
        How can I show a PyQt modal dialog and get data out of its controls once its closed?
        https://stackoverflow.com/questions/18196799/how-can-i-show-a-pyqt-modal-dialog-and-get-data-out-of-its-controls-once-its-clo

        how to clear child window reference stored in parent application when child window is closed?
        https://stackoverflow.com/questions/27420338/how-to-clear-child-window-reference-stored-in-parent-application-when-child-wind
    """

    def __init__(self, parent, fontOptions, _openFileCall, dialogTypeName, dialogTitleMessage):
        super().__init__( parent )
        self.result = 0
        self.setAttribute( Qt.WA_DeleteOnClose )

        self._openFileCall = _openFileCall

        # QWidget::setLayout: Attempting to set QLayout “” on ProgramWindow “”, which already has a layout
        # https://stackoverflow.com/questions/50176661/qwidgetsetlayout-attempting-to-set-qlayout-on-programwindow-which-alre
        self.centralwidget = QWidget()
        self.setCentralWidget( self.centralwidget )

        self.resize( 600, 400  )
        self.setWindowTitle( dialogTitleMessage )

        # nice widget for editing the date
        self.textEditWidget = QPlainTextEdit( self )
        self.textEditWidget.setLineWrapMode( QPlainTextEdit.NoWrap )

        # Detect Ctrl+S ion QTextedit?
        # https://stackoverflow.com/questions/43010630/detect-ctrls-ion-qtextedit
        enterShortcut = QShortcut( QKeySequence( "Ctrl+Enter" ), self.textEditWidget )
        returnShortcut = QShortcut( QKeySequence( "Ctrl+Return" ), self.textEditWidget )
        enterShortcut.activated.connect( self.accept )
        returnShortcut.activated.connect( self.accept )

        # Set initial value of text
        self.textEditWidget.document().setPlainText( wrap_text( """
            # Write your %s here
            # or open it from a new file
        """ % dialogTypeName ) + "\n\n" )

        # Change font, colour of text entry box
        self.textEditWidget.selectAll()
        self.textEditWidget.setStyleSheet( fontOptions )

        # OK and Cancel buttons
        self.standardButtons = QDialogButtonBox( QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self )
        self.openFileButton = QPushButton( "Open a %s from a file" % dialogTypeName )

        self.standardButtons.accepted.connect( self.accept )
        self.standardButtons.rejected.connect( self.reject )
        self.openFileButton.clicked.connect( self.handleOpenFileCall )

        # Setup the main layout
        self.verticalLayout = QVBoxLayout( self.centralwidget )
        self.horizontalLayout = QHBoxLayout()

        self.verticalLayout.addWidget( self.textEditWidget )
        self.verticalLayout.addLayout( self.horizontalLayout )

        self.horizontalLayout.addWidget( self.openFileButton )
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
        # log( 1, "closeEvent" )
        self.event.quit()

    def keyPressEvent(self, event):
        """
            Closes the application when the escape key is pressed.
        """

        if event.key() == PyQt5.QtCore.Qt.Key_Escape:
            self.close()

    @ignore_exceptions
    def handleOpenFileCall(self, qt_decorator_bug):
        inputString = self._openFileCall()
        setTextWithoutCleaningHistory( self.textEditWidget, inputString )

    # static method to create the dialog and return ( date, time, accepted )
    @staticmethod
    def getNewUserInput(parent, fontOptions, _openFileCall, dialogTypeName, dialogTitleMessage):
        dialog = StringInputDialog( parent, fontOptions, _openFileCall, dialogTypeName, dialogTitleMessage )
        result = dialog.exec_()

        # dialog.deleteLater()
        # log( 1, "result: %s", result )
        return ( dialog.textEditWidget.toPlainText(), result == QDialog.Accepted )

