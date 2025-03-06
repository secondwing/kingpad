import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QAction, QFileDialog, QMessageBox

class Notepad(QMainWindow):
    def __init__(self):
        super().__init__()
        self.currentFile = None  # 현재 열려있는 파일의 경로를 저장
        self.initUI()

    def initUI(self):
        # 메인 텍스트 편집 위젯 생성 및 중앙에 배치
        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.statusBar()  # 하단 상태바 생성

        # 메뉴바 생성 및 File 메뉴 추가
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')

        # 새 파일 액션
        newAct = QAction('New', self)
        newAct.setShortcut('Ctrl+N')
        newAct.triggered.connect(self.newFile)

        # 파일 열기 액션
        openAct = QAction('Open', self)
        openAct.setShortcut('Ctrl+O')
        openAct.triggered.connect(self.openFile)

        # 파일 저장 액션
        saveAct = QAction('Save', self)
        saveAct.setShortcut('Ctrl+S')
        saveAct.triggered.connect(self.saveFile)

        # 종료 액션
        exitAct = QAction('Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(self.close)

        # 메뉴에 액션 추가
        fileMenu.addAction(newAct)
        fileMenu.addAction(openAct)
        fileMenu.addAction(saveAct)
        fileMenu.addAction(exitAct)

        # 창의 기본 속성 설정
        self.setWindowTitle('Notepad')
        self.setGeometry(100, 100, 800, 600)
        self.show()

    def newFile(self):
        # 현재 편집 중인 내용이 있으면 저장 여부 확인
        if self.textEdit.toPlainText():
            reply = QMessageBox.question(
                self,
                '저장 확인',
                '저장되지 않은 내용이 있습니다. 저장하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                self.saveFile()
            elif reply == QMessageBox.Cancel:
                return
        self.textEdit.clear()
        self.currentFile = None
        self.statusBar().showMessage("새 파일 생성됨")

    def openFile(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open File', '', "Text Files (*.txt);;All Files (*)")
        if fname:
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    self.textEdit.setText(f.read())
                self.currentFile = fname
                self.statusBar().showMessage(f"Opened {fname}")
            except Exception as e:
                QMessageBox.warning(self, "오류", f"파일을 여는 도중 오류가 발생했습니다:\n{e}")

    def saveFile(self):
        if self.currentFile is None:
            self.currentFile, _ = QFileDialog.getSaveFileName(self, 'Save File', '', "Text Files (*.txt);;All Files (*)")
        if self.currentFile:
            try:
                with open(self.currentFile, 'w', encoding='utf-8') as f:
                    f.write(self.textEdit.toPlainText())
                self.statusBar().showMessage(f"Saved {self.currentFile}")
            except Exception as e:
                QMessageBox.warning(self, "오류", f"파일을 저장하는 도중 오류가 발생했습니다:\n{e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    notepad = Notepad()
    sys.exit(app.exec_())
