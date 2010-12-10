# Duality SVN
# Original Author: Joshua Leung
#
# Svn Commit Dialog - Commit log message construction

from coreDefines import *

from SvnStatusList import *

#########################################

# SVN Commit Dialog
# Prepare commit log for committing some changes. 
#
# TODO: have an alternative interface with fields for structured logs?
class SvnCommitDialog(QDialog):
	# Class Defines ====================================
	# Output filename for temp log file
	LOG_FILENAME = "commitlog.duality.txt"
	
	# Minimum amount of "content" (as num of chars) in log message to be ok
	MIN_LOG_LEN = 3;
	
	# Word-Wrap
	wordWrapper = textwrap.TextWrapper();
	
	# Instance Settings ================================
	__slots__ = (
		'layout',	# (QLayout) layout manager for widget
	);
	
	# Setup ============================================
	
	# ctor
	# < parent: (QWidget) window that owns this dialog
	# < (branchName): (str) string representing the name or URL of the branch changes are getting committed to
	# < (filesList): (SvnStatusListDatalist) list of files that will be involved in the commit
	def __init__(self, parent, branchName, filesList):
		super(SvnCommitDialog, self).__init__(parent);
		
		# toplevel stuff
		self.setWindowTitle("Log Message for Commit - Duality SVN");
		self.setGeometry(150, 150, 600, 400);
		
		# setup UI
		self.layout = QVBoxLayout();
		self.setLayout(self.layout);
		
		self.setupUI(branchName, filesList);
		
		self.validateMessageLength();
		
	# main widget init
	def setupUI(self, branchName, filesList):
		# 1) "staged" files
		gb = QGroupBox("Changes Pending");
		self.layout.addWidget(gb);
		
		grp = QVBoxLayout();
		gb.setLayout(grp);
		
		# 1a) branch target
		grp.addWidget(QLabel("For: " + branchName));
		
		# 1b) list of files - not editable
		self.wFileList = SvnStatusList(filesList);
		self.wFileList.setFocusPolicy(Qt.NoFocus); # otherwise, log mesage doesn't get focus
		grp.addWidget(self.wFileList);
		
		# .............................
		
		# 2) commit log box
		gb = QGroupBox("Log Message");
		self.layout.addWidget(gb);
		
		grp = QVBoxLayout();
		gb.setLayout(grp);
		
		# 2a) choose from previous messages
		# TODO...
		
		# 2b) log message box
		self.wLog = QPlainTextEdit("");	
		self.wLog.textChanged.connect(self.validateMessageLength);
		grp.addWidget(self.wLog);
		
		# ..............................
		
		# 3) ok/cancel
		grp = QDialogButtonBox();
		self.layout.addWidget(grp);
		
		# 3a) ok - aka "commit"
		# TODO: needs validation of commit-log first...
		self.wCommit = grp.addButton("Commit", QDialogButtonBox.AcceptRole);
		self.wCommit.clicked.connect(self.accept);
		
		# 3b) cancel 
		self.wCancel = grp.addButton(QDialogButtonBox.Cancel);
		self.wCancel.clicked.connect(self.reject);
		
	# Callbacks ===========================================
	
	# validate length of commit log to prevent entering bogus commit logs
	def validateMessageLength(self):
		# get log message, and strip off all whitespace
		bareMessage = str(self.getLogMessage()).strip();
		
		# only if there is content, may we continue...
		self.wCommit.setEnabled(len(bareMessage) >= SvnCommitDialog.MIN_LOG_LEN);
		
	# Methods ============================================
	
	# Log Message ----------------------------------------
	
	# get log message as a text string
	def getLogMessage(self):
		return self.wLog.toPlainText();
		
	# write log message to a temp file, and return its path/name
	# fileN: (str) if provided, this will be the name of the file to save to
	#			 otherwise, defaults to SvnCommitDialog.LOG_FILENAME
	def saveLogMessage(self, fileN=None):
		# open file for writing
		if fileN == None:
			fileN = SvnCommitDialog.LOG_FILENAME;
			
		with open(fileN, "w") as f:
			# grab the log message and split into paragraphs (by line breaks)
			logLines = str(self.getLogMessage()).split("\n");
			
			# perform word wrapping on each of these paragraphs before writing
			# so that the email clients can read this nicely
			for paragraph in logLines:
				if len(paragraph):
					lines = SvnCommitDialog.wordWrapper.wrap(paragraph);
					for line in lines:
						f.write("%s\n" % line);
				else:
					f.write('\n');
			
			# finish up
			f.close();
		
		# return full path name
		# FIXME: the directory where this gets dumped should be user defined
		return os.path.join(os.getcwd(), fileN);
	
#########################################
