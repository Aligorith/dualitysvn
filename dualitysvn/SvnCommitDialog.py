# Duality SVN
# Original Author: Joshua Leung
#
# Svn Commit Dialog - Commit log message construction

from coreDefines import *

from SvnOperationProcess import *
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
		'branchName', # (str)
		'branchType', # (BranchType.TYPE_*)
		
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
		# TODO: validation of currently non-commitable, but later ok files needs to be done...
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
		
	# override of 'commit' button
	def accept(self):
		# perform validation of files, including additional action if necessary...
		if self.validatePaths():
			# now perform standard action
			return super(SvnCommitDialog, self).accept();
		else:
			# already rejected...
			pass;
		
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
	
	# Path List Validation ------------------------------------
	
	# make sure all files to be committed are accounted for
	def validatePaths(self):
		# get lists of files to fix up
			# "unversioned" == need to add
		needAdd = self.wFileList.getOperationList().getFiltered(lambda x: x.file_status == SvnStatusListItem.FileStatusMap['?']);
			# "missing" == already deleted from working copy (or manually renamed), just not noted in svn metadata
		needDelete = self.wFileList.getOperationList().getFiltered(lambda x: x.file_status == SvnStatusListItem.FileStatusMap['!']);
			# "conflicted" == resolved?
		needResolve = self.wFileList.getOperationList().getFiltered(lambda x: x.file_status == SvnStatusListItem.FileStatusMap['C']);
		
		# need to do anything?
		if needAdd or needDelete or needResolve:
			# prompt to do cleanups
			msg  = "The following changes will be performed so that committing can proceed:\n\n";
			msg += '  ' + str(len(needAdd)) + " <b>unversioned</b> paths need to be <b>Added</b>\n";
			msg += '  ' + str(len(needDelete)) + " <b>missing</b> paths need to be <b>Deleted</b>\n";
			msg += '  ' + str(len(needResolve)) + " <b>conflicted</b> paths need to be <b>Resolved</b>\n";
			msg += "\nApply these changes?";
			
			reply = QMessageBox.question(self, 'Confirm Changes',
				Qt.convertFromPlainText(msg), 
				QMessageBox.Apply | QMessageBox.Cancel,
				QMessageBox.Apply);
				
			# proceed
			if reply == QMessageBox.Apply:
				# perform validation actions
				self.validatePathsAdd(needAdd);
				self.validatePathsDelete(needDelete);
				self.validatePathsResolve(needResolve);
				
				# can proceed with commit now
				return True;
			else:
				# don't perform actions, so user might want to go back and check
				return False;
		else:
			# don't do anything
			return True;
			
	# helper for validatePaths - add paths that need adding
	def validatePathsAdd(self, files):
		# skip if nothing to do
		if not files:
			return;
		
		# setup svn add process
		ap = SvnOperationProcess(self, "Commit Add");
		
		ap.setupEnv(BranchType.TYPE_TRUNK); # FIXME: this is currently hardcoded, but needs to be able to be passed in 
		
		ap.setOp("add");
		ap.addArgs(SvnOp_Args['add']);
		ap.setTargets(files);
		
		# run operation (blocking style) now
		if not ap.runBlocking():
			print "Error... auto-add failed"
			
	# helper for validatePaths - delete paths that need deleting
	def validatePathsDelete(self, files):
		# skip if nothing to do
		if not files:
			return;
			
		# setup svn delete process
		dp = SvnOperationProcess(self, "Commit Delete");
		
		dp.setupEnv(BranchType.TYPE_TRUNK); # FIXME: this is currently hardcoded, but needs to be able to be passed in 
		
		dp.setOp("delete");
		dp.addArgs(SvnOp_Args['delete']);
		dp.setTargets(files);
		
		# run operation (blocking style) now
		if not dp.runBlocking():
			print "Error... auto-delete failed"
			
	# helper for validatePaths - resolve paths that need resolving
	def validatePathsResolve(self, files):
		# skip if nothing to do
		if not files:
			return;
	
	
	
#########################################
