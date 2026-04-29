import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import DesktopPetWindow

def main():
    app = QApplication(sys.argv)
    # Windowsでタスクバーにアイコンを正しく表示させるためのID設定
    try:
        import ctypes
        myappid = 'mycompany.myproduct.subproduct.version' # 任意
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass
        
    window = DesktopPetWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
