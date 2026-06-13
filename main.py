import sys
import os

# Ensure project root is in path
root = os.path.dirname(os.path.abspath(__file__))
if root not in sys.path:
    sys.path.insert(0, root)

# Also add src to path for PyInstaller bundle
src_dir = os.path.join(root, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from src.ui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt


def main():
    # High-DPI attributes must be set before QApplication is created
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName("OfficeMetaExtractor")
    app.setApplicationVersion("2.0.0")

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
