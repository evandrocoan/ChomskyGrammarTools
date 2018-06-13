#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from PyQt5 import QtGui
from PyQt5 import QtCore

from PyQt5.QtCore import Qt
from debug_tools import getLogger

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, os.path.basename( os.path.dirname( os.path.abspath ( __file__ ) ) ) )


class RunFunctionAsyncThread(QtCore.QThread):
    """
        Dynamically updates the user interface with new sentences generated by the program.
    """
    send_string_signal = QtCore.pyqtSignal( [str] )
    disable_stop_button_signal = QtCore.pyqtSignal()

    def __init__(self, function, results_dialog):
        """
            Qt- What is the difference between new QThread(this) and new QThread()?
            https://stackoverflow.com/questions/46293674/qt-what-is-the-difference-between-new-qthreadthis-and-new-qthread
        """
        QtCore.QThread.__init__(self)
        self.function = function
        self.results_dialog = results_dialog

        if hasattr( function, 'force_first_run' ):
            self.force_first_run = True
        else:
            self.force_first_run = False

        if hasattr( function, 'waiting' ):
            self.waiting = function.waiting
        else:

            def default():
                self.send_string_signal.emit( "Computing... No results available yet... " )
                self.sleep( 1 )

            self.waiting = default

    def run(self):

        class ProcessThread(QtCore.QThread):

            def __init__(self, parent, function):
                QtCore.QThread.__init__(self, parent)
                self.function = function

            def run(self):
                self.function()

        self.process_thread = ProcessThread( self.parent(), self.function )
        self.process_thread.start()

        force_first_run = self.force_first_run
        self.sleep( 1 )

        while self.process_thread.isRunning() or force_first_run:
            force_first_run = False
            self.waiting( self )

            if not self.function.isToStop[0]:
                self.sleep( 1 )

                if self.process_thread.isRunning():
                    self.process_thread.terminate()

        # If it was not stopped by the close event setting isToStop, then append the success message
        self.process_thread.wait()

        if not self.function.isToStop[0]:
            self.disable_stop_button_signal.emit()

            self.send_string_signal.emit( self.function.results )
            set_scroll_to_maximum( self.results_dialog.textEditWidget )


def run_function_async(function, results_dialog):
    """
        Create the updating thread and connect
        it's received signal to append
        every received chunk of data/text will be appended to the text
    """
    qtUpdateThread = RunFunctionAsyncThread( function, results_dialog )
    qtUpdateThread.send_string_signal.connect( results_dialog.appendText )
    qtUpdateThread.disable_stop_button_signal.connect( results_dialog.disableStopButton )
    qtUpdateThread.start()

    # Block QMainWindow while child widget is alive, pyqt
    # https://stackoverflow.com/questions/22410663/block-qmainwindow-while-child-widget-is-alive-pyqt
    results_dialog.setWindowModality( Qt.ApplicationModal )
    results_dialog.show()

    set_scroll_to_maximum( results_dialog.textEditWidget )
    return qtUpdateThread


def set_scroll_to_maximum(textEdit):
    # Autoscroll PyQT QTextWidget
    # https://stackoverflow.com/questions/7778726/autoscroll-pyqt-qtextwidget
    textEdit.moveCursor( QtGui.QTextCursor.End )
    textEdit.moveCursor( QtGui.QTextCursor.StartOfLine )
    textEdit.ensureCursorVisible()

    verticalScrollBar = textEdit.verticalScrollBar()
    horizontalScrollBar = textEdit.horizontalScrollBar()
    verticalScrollBar.setValue( horizontalScrollBar.maximum() )
    horizontalScrollBar.setValue( horizontalScrollBar.minimum() )
