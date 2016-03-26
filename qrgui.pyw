import sys
import io
import logging
from PyQt5.QtWidgets import (
    QWidget, QApplication, QVBoxLayout, QFormLayout, QLineEdit, QLabel,
    QComboBox, QSpinBox)
from PyQt5.QtGui import QImage, QPixmap
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
                text, error, version, mode = self.get_parameters()
                qr = pyqrcode.create(text, error, version, mode)
                logging.info(qr)
                buffer = io.BytesIO()
                qr.png(buffer, scale=6)
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

        error_label = QLabel("&Error", self)
        self.error_box = QComboBox(self)
        self.error_box.addItem("Highest (30%)", "H")
        self.error_box.addItem("Quality (25%)", "Q")
        self.error_box.addItem("Medium (15%)", "M")
        self.error_box.addItem("Low (7%)", "L")

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
        self.mode_box.addItem("Kanji", "kanji")

        form = QFormLayout()
        form.addRow(error_label, self.error_box)
        form.addRow(version_label, self.version_box)
        form.addRow(mode_label, self.mode_box)

        error_label.setBuddy(self.error_box)
        version_label.setBuddy(self.version_box)
        mode_label.setBuddy(self.mode_box)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.line_edit)
        vbox.addWidget(self.label)
        vbox.addLayout(form)

        self.line_edit.textEdited.connect(self.request_new_qr_code)
        self.error_box.currentTextChanged.connect(self.request_new_qr_code)
        self.version_box.valueChanged.connect(self.request_new_qr_code)
        self.mode_box.currentTextChanged.connect(self.request_new_qr_code)

        self.setWindowTitle('QR')
        self.show()

    @pyqtSlot()
    def request_new_qr_code(self):
        self.worker.set_parameters(
            (self.line_edit.text(),
             self.error_box.currentData(),
             self.get_version(),
             self.mode_box.currentData()))

    def draw_qr_code(self, image):
        pixmap = QPixmap.fromImage(image)
        self.label.setPixmap(pixmap)

    def print_error_message(self, message):
        self.label.setText(message)

    def get_version(self):
        v = self.version_box.value()
        if v == 0:
            return None
        else:
            return v

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
