import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("RawStudio")
window.resize(1000, 650)
window.setStyleSheet("background-color: #1e1e1e;")

layout = QVBoxLayout()

label = QLabel("RawStudio")
label.setStyleSheet("color: #ffffff; fontize: 16px;")

layout.addWidget(label)
window.setLayout(layout)

window.show()

sys.exit(app.exec())

