#!/usr/bin/env python3

import sys
import io
import logging
from PyQt5.QtWidgets import (
    QWidget, QApplication, QVBoxLayout, QFormLayout, QLineEdit, QLabel,
    QComboBox, QSpinBox, QFileDialog, QAction, QScrollArea, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import (
    Qt, pyqtSlot, pyqtSignal, QThread, QSemaphore, QMutex, QMutexLocker)
import pyqrcode


class WorkerThread(QThread):

    resultReady = pyqtSignal('QImage')
    errorOccurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.semaphore = QSemaphore()
        self.mutex = QMutex()
        self.parameters = None

    def run(self):
        while True:
            try:
                text, error, version, mode, scale = self.get_parameters()
                qr = pyqrcode.create(text, error, version, mode)
                logging.info(qr)
                buffer = io.BytesIO()
                qr.png(buffer, scale=scale)
                image = QImage.fromData(buffer.getvalue())
                self.resultReady.emit(image)
            except ValueError as e:
                logging.warning(e)
                self.errorOccurred.emit(str(e))

    def set_parameters(self, parameters):
        with QMutexLocker(self.mutex):
            self.parameters = parameters
            if self.semaphore.available() == 0:
                self.semaphore.release(1)

    def get_parameters(self):
        self.semaphore.acquire(1)
        with QMutexLocker(self.mutex):
            parameters = self.parameters
            self.parameters = None
            return parameters


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.init_thread()
        self.init_ui()

        self.request_new_qr_code()

    def init_thread(self):
        self.worker = WorkerThread(self)
        self.worker.resultReady.connect(self.draw_qr_code)
        self.worker.errorOccurred.connect(self.print_error_message)
        self.worker.start()

    def init_ui(self):
        self.line_edit = QLineEdit(self)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignHCenter)

        self.save_action = QAction("&Save", self)
        self.about_action = QAction("&About...", self)
        self.label.addAction(self.save_action)
        self.label.addAction(self.about_action)
        self.label.setContextMenuPolicy(Qt.ActionsContextMenu)

        scroll_area = QScrollArea()
        scroll_area.setWidget(self.label)
        scroll_area.setWidgetResizable(True)

        error_correction_label = QLabel("&Error Correction", self)
        self.error_correction_box = QComboBox(self)
        self.error_correction_box.addItem("High (30%)", "H")
        self.error_correction_box.addItem("Quartile (25%)", "Q")
        self.error_correction_box.addItem("Medium (15%)", "M")
        self.error_correction_box.addItem("Low (7%)", "L")

        version_label = QLabel("&Version", self)
        self.version_box = QSpinBox(self)
        self.version_box.setMinimum(0)
        self.version_box.setMaximum(40)
        self.version_box.setSpecialValueText("Automatic")

        mode_label = QLabel("&Mode", self)
        self.mode_box = QComboBox(self)
        self.mode_box.addItem("Automatic", None)
        self.mode_box.addItem("Numeric", "numeric")
        self.mode_box.addItem("Alphanumeric", "alphanumeric")
        self.mode_box.addItem("Binary", "binary")

        scale_label = QLabel("&Scale", self)
        self.scale_box = QSpinBox(self)
        self.scale_box.setMinimum(1)
        self.scale_box.setMaximum(10)
        self.scale_box.setValue(5)

        form = QFormLayout()
        form.addRow(error_correction_label, self.error_correction_box)
        form.addRow(version_label, self.version_box)
        form.addRow(mode_label, self.mode_box)
        form.addRow(scale_label, self.scale_box)

        error_correction_label.setBuddy(self.error_correction_box)
        version_label.setBuddy(self.version_box)
        mode_label.setBuddy(self.mode_box)
        scale_label.setBuddy(self.scale_box)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.line_edit)
        vbox.addWidget(scroll_area)
        vbox.addLayout(form)

        self.save_action.triggered.connect(self.save_image)
        self.about_action.triggered.connect(self.show_about_message)

        self.line_edit.textEdited.connect(self.request_new_qr_code)
        self.error_correction_box.currentTextChanged.connect(
            self.request_new_qr_code)
        self.version_box.valueChanged.connect(self.request_new_qr_code)
        self.mode_box.currentTextChanged.connect(self.request_new_qr_code)
        self.scale_box.valueChanged.connect(self.request_new_qr_code)

        self.setWindowTitle(QApplication.applicationName())
        self.setWindowIcon(QIcon('icon.png'))

    @pyqtSlot()
    def request_new_qr_code(self):
        self.worker.set_parameters(
            (self.line_edit.text(),
             self.error_correction_box.currentData(),
             self.get_version(),
             self.mode_box.currentData(),
             self.scale_box.value()))

    @pyqtSlot()
    def save_image(self):
        filename, ok = QFileDialog.getSaveFileName(
            self, "Save QR code to PNG image", ".", "PNG Images (*.png)")
        if ok:
            pixmap = self.label.pixmap()
            pixmap.save(filename)

    @pyqtSlot()
    def show_about_message(self):
        message = "%s %s<br>\nDeveloped by <a href=\"%s\">%s</a>" % (
            QApplication.applicationName(),
            QApplication.applicationVersion(),
            QApplication.organizationDomain(),
            QApplication.organizationName()
        )
        QMessageBox.about(self, None, message)

    def draw_qr_code(self, image):
        pixmap = QPixmap.fromImage(image)
        self.label.setPixmap(pixmap)
        self.save_action.setEnabled(True)

    def print_error_message(self, message):
        self.label.setText(message)
        self.save_action.setEnabled(False)

    def get_version(self):
        v = self.version_box.value()
        if v == 0:
            return None
        else:
            return v


def main():
    application = QApplication(sys.argv)
    application.setApplicationName("QR Encoder")
    application.setApplicationVersion("1.0")
    application.setOrganizationName("Claudio Mattera")
    application.setOrganizationDomain(
        "https://github.com/claudio-mattera/qr-encoder")
    main_window = MainWindow()
    main_window.show()
    sys.exit(application.exec_())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
