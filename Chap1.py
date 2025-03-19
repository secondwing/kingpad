import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QAction, QFileDialog, QMessageBox,
    QSplitter, QFileSystemModel, QTreeView, QTabWidget, QInputDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from git import Repo, InvalidGitRepositoryError

class EditorTab(QTextEdit):
    def __init__(self, file_path=None):
        super().__init__()
        self.file_path = file_path
        if file_path:
            self.load(file_path)

    def load(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            self.setText(f.read())
        self.file_path = path

    def save(self, path=None):
        if path:
            self.file_path = path
        if self.file_path:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.toPlainText())
            return True
        return False

class Kingpad(QMainWindow):
    def __init__(self):
        super().__init__()
        self.projectPath = None
        self.repo = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Kingpad')
        self.setWindowIcon(QIcon('kingpad_icon.png'))
        self.setGeometry(100, 100, 1000, 700)

        self.splitter = QSplitter(Qt.Horizontal)
        self.model = QFileSystemModel()
        self.tree = QTreeView()
        self.tree.doubleClicked.connect(self.open_from_tree)
        self.tabs = QTabWidget()
        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.tabs)
        self.setCentralWidget(self.splitter)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')
        projectMenu = menubar.addMenu('Project')
        editMenu = menubar.addMenu('Edit')
        gitMenu = menubar.addMenu('Git')

        # File Actions
        newAct = QAction('New File', self); newAct.setShortcut('Ctrl+N'); newAct.triggered.connect(self.new_tab)
        openAct = QAction('Open File', self); openAct.setShortcut('Ctrl+O'); openAct.triggered.connect(self.open_file_dialog)
        saveAct = QAction('Save', self); saveAct.setShortcut('Ctrl+S'); saveAct.triggered.connect(self.save_file)
        exitAct = QAction('Exit', self); exitAct.setShortcut('Ctrl+Q'); exitAct.triggered.connect(self.close)
        for act in (newAct, openAct, saveAct, exitAct): fileMenu.addAction(act)

        # Project Actions
        openProjAct = QAction('Open Folder', self); openProjAct.triggered.connect(self.open_project)
        projectMenu.addAction(openProjAct)

        # Edit Actions
        zoomInAct = QAction('Zoom In', self); zoomInAct.setShortcut('Ctrl++'); zoomInAct.triggered.connect(lambda: self.current_editor().zoomIn())
        zoomOutAct = QAction('Zoom Out', self); zoomOutAct.setShortcut('Ctrl+-'); zoomOutAct.triggered.connect(lambda: self.current_editor().zoomOut())
        for act in (zoomInAct, zoomOutAct): editMenu.addAction(act)

        # Git Actions
        commitAct = QAction('Commit', self); commitAct.triggered.connect(self.commit_dialog)
        checkoutAct = QAction('Checkout', self); checkoutAct.triggered.connect(self.checkout_dialog)
        gitMenu.addAction(commitAct); gitMenu.addAction(checkoutAct)

        self.statusBar()
        self.show()

    def new_tab(self):
        editor = EditorTab()
        idx = self.tabs.addTab(editor, 'Untitled')
        self.tabs.setCurrentIndex(idx)

    def open_file_dialog(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'Text Files (*.txt);;All Files (*)')
        if fname:
            self.open_file(fname)

    def open_from_tree(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            self.open_file(path)

    def open_file(self, path):
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if editor.file_path == path:
                self.tabs.setCurrentIndex(i)
                return
        editor = EditorTab(path)
        self.tabs.addTab(editor, os.path.basename(path))
        self.tabs.setCurrentIndex(self.tabs.count() - 1)

    def save_file(self):
        editor = self.current_editor()
        if editor:
            if not editor.file_path:
                fname, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 'Text Files (*.txt);;All Files (*)')
                if fname:
                    editor.save(fname)
                    self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(fname))
            else:
                editor.save()
            self.statusBar().showMessage(f'Saved {editor.file_path}')

    def current_editor(self):
        return self.tabs.currentWidget() if self.tabs.count() else None

    def open_project(self):
        folder = QFileDialog.getExistingDirectory(self, 'Open Project')
        if folder:
            self.projectPath = folder
            self.model.setRootPath(folder)
            self.tree.setModel(self.model)
            self.tree.setRootIndex(self.model.index(folder))
            try:
                self.repo = Repo(folder)
            except InvalidGitRepositoryError:
                self.repo = Repo.init(folder)
            self.statusBar().showMessage(f'Project: {folder}')

    def commit_dialog(self):
        if not self.repo:
            return QMessageBox.warning(self, 'Git Error', 'No Git repository')
        msg, ok = QInputDialog.getText(self, 'Commit', 'Message:')
        if ok and msg.strip():
            self.repo.index.add([self.current_editor().file_path])
            self.repo.index.commit(msg)
            self.statusBar().showMessage('Committed ✔')

    def checkout_dialog(self):
        if not self.repo:
            return QMessageBox.warning(self, 'Git Error', 'No Git repository')
        commits = [f'{c.hexsha[:7]} - {c.message.strip()}' for c in self.repo.iter_commits()]
        choice, ok = QInputDialog.getItem(self, 'Checkout', 'Select commit:', commits, 0, False)
        if ok:
            sha = choice.split()[0]
            self.repo.git.checkout(sha)
            self.statusBar().showMessage(f'Checked out {sha}')
            editor = self.current_editor()
            if editor and editor.file_path:
                editor.load(editor.file_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Kingpad()
    sys.exit(app.exec_())
