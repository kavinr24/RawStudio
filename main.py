import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("RawStudio")
window.resize(1000,650)

label = QLabel("RawStudio",parent=window)
label.move(450,300)

window.show()
sys.exit(app.exec())