import sys, os, keyword, re
from PyQt5.QtWidgets import (
  QApplication, QMainWindow, QTextEdit, QAction, QFileDialog, QMessageBox,
  QSplitter, QFileSystemModel, QTreeView, QTabWidget, QInputDialog, QLabel,
  QScrollArea 
)
from PyQt5.QtGui import QIcon, QSyntaxHighlighter, QTextCharFormat, QColor, QPixmap, QImage
from PyQt5.QtCore import Qt
from git import Repo, InvalidGitRepositoryError

class ImageTab(QScrollArea):
  def __init__(self, file_path=None):
    super().__init__()
    self.file_path = file_path
    self.scale = 1.0
    
    # 이미지를 표시할 라벨 생성
    self.imageLabel = QLabel()
    self.imageLabel.setScaledContents(True)
    self.setWidget(self.imageLabel)
    
    # 스크롤바 설정
    self.setWidgetResizable(True)
    self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    
    if file_path:
      self.load(file_path)

  def load(self, path):
    self.file_path = path
    self.original_pixmap = QPixmap(path)
    self.update_image()

  def update_image(self):
    # 현재 스케일에 맞춰 이미지 크기 조정 (정수형으로 변환)
    scaled_width = int(self.original_pixmap.width() * self.scale)
    scaled_height = int(self.original_pixmap.height() * self.scale)
    
    # 최소 크기 설정
    scaled_width = max(1, scaled_width)
    scaled_height = max(1, scaled_height)
    
    self.imageLabel.setFixedSize(scaled_width, scaled_height)
    self.imageLabel.setPixmap(self.original_pixmap.scaled(
      scaled_width,
      scaled_height,
      Qt.KeepAspectRatio,
      Qt.SmoothTransformation
    ))

  def wheelEvent(self, event):
    if event.modifiers() & Qt.ControlModifier:
      delta = event.angleDelta().y()
      # 확대/축소 비율 조정 (10%씩)
      if delta > 0:
        self.scale *= 1.1
      else:
        self.scale *= 0.9
      # 최소/최대 스케일 제한
      self.scale = max(0.1, min(5.0, self.scale))
      self.update_image()
    else:
      # 일반 스크롤
      super().wheelEvent(event)
      
class PythonHighlighter(QSyntaxHighlighter):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.highlighting_rules = []
    
    # Python 키워드 강조
    keyword_format = QTextCharFormat()
    keyword_format.setForeground(QColor("#FF6B6B"))  # 빨간색 계열
    font = keyword_format.font()
    font.setBold(True)
    keyword_format.setFont(font) 
    keywords = [f'\\b{w}\\b' for w in keyword.kwlist]
    for word in keywords:
      self.highlighting_rules.append((re.compile(word), keyword_format))

    # 문자열 강조
    string_format = QTextCharFormat()
    string_format.setForeground(QColor("#98C379"))  # 초록색 계열
    self.highlighting_rules.append((re.compile('"[^"\\\\]*(\\\\.[^"\\\\]*)*"'), string_format))
    self.highlighting_rules.append((re.compile("'[^'\\\\]*(\\\\.[^'\\\\]*)*'"), string_format))

    # 주석 강조
    comment_format = QTextCharFormat()
    comment_format.setForeground(QColor("#5C6370"))  # 회색 계열
    self.highlighting_rules.append((re.compile('#[^\n]*'), comment_format))

    # 함수/클래스 이름 강조
    function_format = QTextCharFormat()
    function_format.setForeground(QColor("#61AFEF"))  # 파란색 계열
    font = function_format.font()
    font.setBold(True)
    function_format.setFont(font) 

    # 함수 정의 패턴 수정
    self.highlighting_rules.append((re.compile('\\bdef\\s+(\\w+)'), function_format))
    # 클래스 정의 패턴 수정
    self.highlighting_rules.append((re.compile('\\bclass\\s+(\\w+)'), function_format))

  def highlightBlock(self, text):
    for pattern, format in self.highlighting_rules:
      for match in pattern.finditer(text):
        self.setFormat(match.start(), match.end() - match.start(), format)

class EditorTab(QTextEdit):
  def __init__(self, file_path=None):
    super().__init__()
    self.file_path = file_path
    self.setMouseTracking(True)
    self.highlighter = PythonHighlighter(self.document())
    self.base_font_size = self.font().pointSize()
    self.zoom_level = 0

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

  def wheelEvent(self, event):
    if event.modifiers() & Qt.ControlModifier:
      delta = event.angleDelta().y()
      if delta > 0:
        self.zoomIn()
        self.zoom_level += 1
      else:
        self.zoomOut()
        self.zoom_level -= 1
      # 상태바 업데이트를 위해 메인 윈도우까지 찾아가기
      current_size = self.base_font_size + self.zoom_level
      main_window = self.get_main_window()
      if main_window:
        main_window.update_font_size(current_size)
    else:
      super().wheelEvent(event)

  def get_main_window(self):
    # 부모 위젯을 따라가면서 Kingpad 인스턴스 찾기
    parent = self.parent()
    while parent is not None:
      if isinstance(parent, Kingpad):
        return parent
      parent = parent.parent()
    return None

class Kingpad(QMainWindow):
  def __init__(self):
    super().__init__()
    self.projectPath = None
    self.repo = None
    self.initUI()
    self.new_tab()

  def initUI(self):
    self.setWindowTitle('Kingpad')
    self.setWindowIcon(QIcon('kingpad_icon.png'))
    self.setGeometry(100, 100, 1000, 700)

    self.splitter = QSplitter(Qt.Horizontal)
    self.model = QFileSystemModel()
    self.tree = QTreeView()
    self.tree.doubleClicked.connect(self.open_from_tree)
    self.tabs = QTabWidget()
    # 탭 닫기 버튼 활성화
    self.tabs.setTabsClosable(True)
    self.tabs.tabCloseRequested.connect(self.close_tab)
    self.splitter.addWidget(self.tree)
    self.splitter.addWidget(self.tabs)
    # 스플리터 비율 설정 (20:80)
    self.splitter.setSizes([200, 800])
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

    self.statusBar().showMessage('Font Size: Default')
    self.show()

  def new_tab(self):
    editor = EditorTab()
    idx = self.tabs.addTab(editor, 'Untitled')
    self.tabs.setCurrentIndex(idx)

  def open_file_dialog(self):
    # 파일 형식 필터 확장
    filters = (
      'Python Files (*.py);;'
      'Text Files (*.txt);;'
      'HTML Files (*.html *.htm);;'
      'CSS Files (*.css);;'
      'JavaScript Files (*.js);;'
      'JSON Files (*.json);;'
      'Markdown Files (*.md *.markdown);;'
      'Image Files (*.png *.jpg *.jpeg *.gif *.bmp);;'
      'All Files (*)'
    )
    fname, _ = QFileDialog.getOpenFileName(self, 'Open File', '', filters)
    if fname:
      self.open_file(fname)

  def open_from_tree(self, index):
    path = self.model.filePath(index)
    if os.path.isfile(path):
      self.open_file(path)

  def open_file(self, path):
    for i in range(self.tabs.count()):
      editor = self.tabs.widget(i)
      if getattr(editor, 'file_path', None) == path:
        self.tabs.setCurrentIndex(i)
        return

    # 파일 확장자 확인
    ext = os.path.splitext(path)[1].lower()
    if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
      # 이미지 파일인 경우
      tab = ImageTab(path)
    else:
      # 텍스트 파일인 경우
      tab = EditorTab(path)

    self.tabs.addTab(tab, os.path.basename(path))
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

  def close_tab(self, index):
    self.tabs.removeTab(index)

  def update_font_size(self, size):
    self.statusBar().showMessage(f'Font Size: {size}pt')

if __name__ == '__main__':
  app = QApplication(sys.argv)
  window = Kingpad()
  sys.exit(app.exec_())
