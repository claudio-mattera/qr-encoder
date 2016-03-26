import sys
import io
from PyQt5.QtWidgets import (
    QWidget, QApplication, QVBoxLayout, QLineEdit, QLabel)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, pyqtSlot
import pyqrcode


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.line_edit = QLineEdit(self)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignHCenter)
        self.line_edit.textEdited.connect(self.on_text_edited)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.line_edit)
        vbox.addWidget(self.label)

        self.setWindowTitle('QR')
        self.show()

    @pyqtSlot(str)
    def on_text_edited(self, text):
        qr = pyqrcode.create(text)
        print(qr)
        buffer = io.BytesIO()
        qr.png(buffer, scale=6)
        image = QImage.fromData(buffer.getvalue())
        pixmap = QPixmap.fromImage(image)
        self.label.setPixmap(pixmap)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
