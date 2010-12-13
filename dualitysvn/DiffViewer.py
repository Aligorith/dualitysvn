# Duality SVN
# Original Author: Joshua Leung
#
# Diff Viewer - View a set of changes

from coreDefines import *

#########################################
# Diff Presentation Widget

# FIXME: this is currently just a wrapper, but later this should get some
# special drawing capabilities too!

class DiffWidget(QTextBrowser):
	def __init__(self, parent):
		super(DiffWidget, self).__init__(parent);
		
		# set tab width - 4 cw's please!
		self.setTabStopWidth(self.cursorWidth()*4*5);


#########################################
# Diff Viewer Window

class DiffViewer(QMainWindow):
	
	# Setup ================================================
	
	# ctors
	def __init__(self, parent=None):
		super(DiffViewer, self).__init__(parent);
		
		# window settings
		self.setWindowTitle("Duality Diff Viewer");
		self.setGeometry(150, 150, 600, 400);
		
		# setup UI
		self.setupUI();
		
	# set up main widgets 
	def setupUI(self):
		# dummy widget for MainWindow container
		dw = QWidget();
		self.setCentralWidget(dw);
		
		# main layout container
		self.layout = QVBoxLayout();
		dw.setLayout(self.layout);
		
		# ..........
		
		# just have a big text-box showing the diff for now
		self.wDisplay = DiffWidget(self);
		
		self.layout.addWidget(self.wDisplay);
		
	# Methods =============================================
	
	# display a diff obtained from internal actions
	def displayDiff_fromString(self, txt):
		# set as new contents
		self.wDisplay.clear();
		self.wDisplay.insertPlainText(txt);

#########################################
