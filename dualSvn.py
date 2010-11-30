# = Dual SVN =
# == What ==
# A helper utility to create a new SVN branch that gets updated easily
# by having the working copy simultaneously being tagged/having
# metadata for two branches in the same SVN tree, with this duality
# being managed by this utility.
#
# == How ==
# This utility is designed for the case where you have a situation where
# you've got 2 "branches" where development is taking place: a "trunk" and
# a "development branch".
#
# Assuming you've already got a working copy of "trunk" set up, ready to be 
# branched, this utility can then be used to set up a branch in the repository
# and at the same time set up your working copy to be able to:
#	1) commit to either the branch or the trunk
#	2) recieve updates made in either the branch or the trunk with no more effort 
#	   than a "standard update" would entail
#
# == This File ==
# This file is the main script, although additional helper files are also
# generated as necessary to facilitate various processes.
#
# == Key History ==
# Original Author: Joshua Leung (aligorith@gmail.com)
# Coded: November 2010

##########################################
# Core Methods

import sys

import os
import shutil

import textwrap

# --------------------------------
# Top Level Defines

# folder names where svn keeps its meta data for the two branches
SVN_DIRNAME_BRANCH1 = ".svn"
SVN_DIRNAME_BRANCH2 = "_svn"

# environment variable that is set to allow this behaviour to work
SVN_HACK_ENVVAR = 'SVN_ASP_DOT_NET_HACK';

# --------------------------------
# OS-Level Utilities

# run some command without any shell interaction
def OSU_runCommand(cmd):
	status = os.system(cmd)
	
	if status: 
		print "Exited with Error No: ", status
		#raise "Runtime Error"

# Switch to/from secondary branch
def OSU_branch2Enable(on=True):
	if on:
		os.environ[SVN_HACK_ENVVAR] = 1;
	else:
		if HACKVAR in os.environ:
			del os.environ[SVN_HACK_ENVVAR];
			
# Status updates...
# TODO: this only works for console version for now
def status(str):
	print str;

# --------------------------------
# Utility Methods

# Duplicate all ".svn" folders (and their contents) to "_svn" ones recursively
# - Used for setting up local copy of branch
#
# < root: (str) path to directory where root of source tree resides
# > return[0]: (list) summary of errors that occurred during this process (description+path)
def duplicateSvnMetadata(root):
	# error stack
	errors = [];
	
	# traverse directory tree
	# 	- p: (str) path of the current directory being traversed
	#	- d: (list<str>) names of directories in current directory being traversed
	#	- f: (list<str>) names of files in current directory
	for p,d,f in os.walk(root):
		# at each directory level, we can perform a copy if the data is present
		# BUT we mustn't ever enter one of these subdirs that we're handling
		if SVN_DIRNAME_BRANCH1 in d:
			d.remove(SVN_DIRNAME_BRANCH1);
			
			# we have a target directory to copy, so copy it
			shutil.copytree(os.path.join(p, SVN_DIRNAME_BRANCH1), os.path.join(p, SVN_DIRNAME_BRANCH2));
		elif SVN_DIRNAME_BRANCH2 in d:
			d.remove(SVN_DIRNAME_BRANCH2);
			
			# only target directory exists, so we've got an error
			errors.append(("Path only has target directory. Inconsistent repository copy.", p));
		else:
			# data not present... skip this directory
			pass;
			
	# return list of errors
	return errors;

# --------------------------------
# System Behaviour

# Setup a new branch, assuming all links are valid
# < srcdir: (str) directory where "trunk" working copy is located
# < target: (str) URL for where the branch should be created in the repository
# < branchName: (str) name of the new branch (to add to svn)
def createBranch(srcdir, target, branchName):
	# make a copy of the existing svn metadata - i.e. setup "trunk" copy as "branch2"
	status("Setting up Working Copy Duality...")
	duplicateSvnMetadata(srcdir);
	
	# perform an "svn copy" operation to make a new branch on the repository
	# 	WC + URL = instant commit 
	status("Branching Commit Pending...");
	cmd = 'svn co "%(sd)s" %(tar)s -m "%(cm)s"' % {'sd':srcdir, 'tar':target, 'cm':"Creating '%s' branch"%(branchName)}
	OSU_runCommand(cmd); 
	
	# change working copy to the branch now
	status("Switching Working Copy to New Branch...");
	cmd = 'svn switch %s' % (target)
	OSU_runCommand(cmd);

# Update working copy
# < srcdir: (str) directory where working copy is located
# < fromBranch2: (bool) should changes be pulled from secondary branch (i.e. "trunk")
def updateWorkingCopy(srcdir, fromBranch2):
	# switch branch?
	OSU_branch2Enable(fromBranch2);
	
	# perform updates
	cmd = 'svn up'
	OSU_runCommand(cmd); # FIXME: need to get output of this one!
	
	# switch back branches - always off, just in case
	OSU_branch2Enable(false);
	
# Perform a svn commit
def commitChanges(filesList, logMessage):
	# add all files in the files list to a new "changeset"
	pass;

###########################################
# UI

import PyQt4

from PyQt4.QtCore import *
from PyQt4.QtGui import *

# -----------------------------------------
# Extended Widgets

# Text Field with a Label
class LabelledTextWidget(QWidget):
	__slots__ = (
		'readCallback', 	# (fn(obj)=str) callback function to get (as a string) the value of the property
		'writeCallback', 	# (fn(obj,str)) callback function which writes the value in the textfield back to the property
		
		'modelObj',			# (obj) object where text data is stored
		
		'wLabel',	# (QLabel) label for text box
		'wText',	# (QLineEdit) text box control
	);
	
	# Setup =========================================
	
	# ctor
	# < name: (str) label to display for this field (does not need to be terminated with ':')
	# < txt: (str) default text to display in the field
	# < tooltip: (str) help text to display
	def __init__ (self, name, txt, tooltip):
		QWidget.__init__(self);
		
		# init self
		self.setToolTip(tooltip);
		
		# placeholders for callbacks
		self.modelObject = None;
		self.readCallback = None;
		self.writeCallback = None;
		
		# create widgets and bind events
			# label
		self.wLabel = QLabel(name + ":");
			# text box
		self.wText = QLineEdit(txt);
		self.wText.textChanged.connect(self.writeOutVal);
		
		# init layout
		layout = QFormLayout();
		self.setLayout(layout);
		
		# add components to layout
		layout.addRow(self.wLabel, self.wText);

	# Methods =========================================
	
	# set model
	def bindModel(self, model):
		# set model
		self.modelObject = model;
		
		# try to flush
		self.readInVal();
	
	# bind callback functions to get values from source and write changes back
	# < readValFunc: (fn(obj)=str) callback function to get (as a string) the value of the property
	# > writeValFunc: (fn(obj,str)) callback function which writes the value in the textfield back to the property
	def bindCallbacks(self, readValFunc, writeValFunc):
		self.readCallback = readValFunc;
		self.writeCallback = writeValFunc;
		
	# wrappers for our callbacks
	def readInVal(self):
		if self.readCallback and self.modelObject:
			self.wText.setText(self.readCallback(self.modelObject));
	
	def writeOutVal(self):
		if self.writeCallback and self.modelObject:
			self.writeCallback(self.modelObject, self.wText.getText());

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Visualise output from SVN operations as a list
class SvnOperationList(QTreeView):
	def __init__(self):
		super(SvnOperationList, self).__init__();
		
		# view setup settings
		self.setRootIsDecorated(False);
		self.setAlternatingRowColors(True);
		
		# model settings
		
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Data item that occurs in SvnStatusList's model

# Show "status" of files/directories within working copy,
# allowing some to be included/excluded from SVN operations
class SvnStatusList(QTreeView):
	# Setup =============================================
	
	def __init__(self):
		super(SvnStatusList, self).__init__();
		
		# view setup settings
		self.setRootIsDecorated(False);
		self.setAlternatingRowColors(True);
		
		# model settings
		

# -----------------------------------------
# Dialogs 

# SVN Operation Dialog
class SvnOperationDialog(QDialog):
	# Class Defines ====================================
	# status of process
	STATUS_WORKING, STATUS_DONE, STATUS_FAILED = range(3);
	
	# Setup ============================================
	
	# ctor
	def __init__(self, parent, opName):
		super(SvnOperationDialog, self).__init__(parent);
		
		# init status
		self.opName = opName;
		self.status = SvnOperationDialog.STATUS_WORKING;
		self.args = [];
		
		# toplevel stuff
		self.setupProcess();
		self.setName();
		
		# setup UI
		self.layout = QVBoxLayout();
		self.setLayout(self.layout);
		
		self.setupUI();
		
	# main widget setup
	def setupUI(self):
		# 1) progress log group 
		gb = QGroupBox("Progress...");
		self.layout.addWidget(gb);
		
		grp = QGridLayout();
		gb.setLayout(grp);
		
		# 1a) progress log box
		self.wStatus = SvnOperationList();
		grp.addWidget(self.wStatus, 1,1); # r1 c1
		
		# 1b) progress bar?
		# TODO
		
		# 3) ok/cancel
		grp = QDialogButtonBox();
		self.layout.addWidget(grp);
		
		# 3a) ok
		# TODO: needs validation that settings are doen
		self.wOk = grp.addButton(QDialogButtonBox.Ok);
		self.wOk.setEnabled(False);
		self.wOk.clicked.connect(self.accept);
		
		# 3b) cancel 
		self.wCancel = grp.addButton(QDialogButtonBox.Cancel);
		self.wCancel.clicked.connect(self.reject);
		
	# setup "process" for grabbing stuff from
	def setupProcess(self):
		# create process object - reuse for every instance...
		self.process = QProcess();
		
		# attach callbacks
		self.connect(self.process, SIGNAL("readyReadStandardOutput()"), self.readOutput);
		self.connect(self.process, SIGNAL("readyReadStandardError()"), self.readErrors);
		self.connect(self.process, SIGNAL("processExited()"), self.pexited);
		
	# Methods ==========================================
	
	# External Setup API ------------------------------
	
	# Add a list of arguments to be passed to svn when running it
	# args: (list<str>) list of arguments to run
	def addArgs(self, args):
		self.args += args;
		
	# Working directory and environment settings
	def setupEnv(self, env):
		pass;
		
	# Start running the svn operation
	def go(self):
		self.startProcess();
	
	# Internal ---------------------------------------
	
	# Set name of dialog, as displayed in the titlebar
	def setName(self):
		if self.status == SvnOperationDialog.STATUS_WORKING:
			self.setWindowTitle(self.opName + " in Progress... - Duality SVN");
		elif self.status == SvnOperationDialog.STATUS_DONE:
			self.setWindowTitle(self.opName + " Done! - Duality SVN");
		else:
			self.setWindowTitle(self.opName + " Error! - Duality SVN");
			
	# Callbacks ======================================
	
	# Process ----------------------------------------
	
	def startProcess(self):
		# try and start the process now
		self.process.start("svn", self.args);
		
		if self.process.state() == QProcess.NotRunning:
			# msgbox warning about error
			QMessageBox.warning(self,
				"SVN Error",
				"Could perform %s operation" % (self.opName));
		
	def endProcess(self):
		# kill process - only way to get rid of console apps on windows
		self.process.kill();
	
	def readOutput(self):
		line = str(self.process.readLine()).rstrip("\n");
		self.wStatus.appendFromStr(line);
	
	def readErrors(self):
		#self.wStatus.appendFromStr("Error: " + QString(self.process.readStderr()));
		pass;
		
	# Buttons ------------------------------------------
	
	# callback called when cancelling dialog
	def reject(self):
		# end the process first
		self.endProcess();
		# TODO: feedback on whether this succeeded
		
		# now, cancel the dialog using it's own version
		super(SvnOperationDialog, self).reject();
		
	# callback called when svn operation process ends
	def pexited(self):
		# if exited with some problem, make sure we warn
		# TODO: set own status codes...?
		if self.process.exitStatus() == QProcess.CrashExit:
			QMessageBox.warning(self,
				"SVN Error",
				"%s operation was not completed successfully" % (self.opName));
		
		# enable the "done" button now, and disable cancel (not much we can do)
		self.wOk.setEnabled(True);
	
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	
# SVN Commit Dialog
# Prepare commit log for committing some changes. 
#
# TODO: have an alternative interface with fields for structured logs?
class SvnCommitDialog(QDialog):
	# Class Defines ====================================
	# Output filename for temp log file
	LOG_FILENAME = "commitlog.duality.txt"
	
	# Word-Wrap
	wordWrapper = textwrap.TextWrapper();
	
	# Instance Settings ================================
	__slots__ = (
		'layout',	# (QLayout) layout manager for widget
	);
	
	# Setup ============================================
	
	# ctor
	def __init__(self, parent):
		super(SvnCommitDialog, self).__init__(parent);
		
		# toplevel stuff
		self.setWindowTitle("Commit");
		
		# setup UI
		self.layout = QVBoxLayout();
		self.setLayout(self.layout);
		
		self.setupUI();
		
	# main widget init
	def setupUI(self):
		# 1) "staged" files
		gb = QGroupBox("Changes Pending");
		self.layout.addWidget(gb);
		
		grp = QVBoxLayout();
		gb.setLayout(grp);
		
		# FIXME: placeholder
		grp.addWidget(QLabel("Target Branch: " + "branchName"));
		
		# .............................
		
		# 2) commit log box
		gb = QGroupBox("Log Message");
		self.layout.addWidget(gb);
		
		grp = QVBoxLayout();
		gb.setLayout(grp);
		
		# 2a) choose from previous messages
		# TODO...
		
		# 2b) log message box
		self.wLog = QTextEdit("");
		self.wLog.setAcceptRichText(False);
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
		
	# Methods ============================================
	
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
		f = open(fileN, "w");
		
		# grab the log message and split into paragraphs (by line breaks)
		logLines = self.getLogMessage().split("\n");
		
		# perform word wrapping on each of these paragraphs before writing
		# so that the email clients can read this nicely
		for paragraph in logLines:
			lines = SvnCommitDialog.wordWrapper.wrap(paragraph);
			for line in lines:
				f.write("%s\n" % line);
		
		# finish up
		f.close();
		return fileN;

# -----------------------------------------
# Branch Panes

# Base define for a pane describing a branch
class BranchPane(QWidget):
	# Class Defines ========================================================
	# Type/Status of Branch
	TYPE_TRUNK, TYPE_TRUNK_REF, TYPE_BRANCH = range(3);
	
	# Instance Settings ====================================================
	__slots__ = (
		# Model .......................................................
		'branchType',		# (int) type of the branch (BranchPane.TYPE_*)
		
		# General Layout Stuff ........................................
		'layout',			# (QLayout) layout manager for widget
		
		# Widgets Stuff ...............................................
		'wUrl',				# (LabelledTextWidget) url of branch in repository
		'wUpdate',			# (QPushButton) svn update
		'wApplyPatch',  	# (QPushButton) apply patch
		
		'wRefreshStatus',  	# (QPushButton) refresh status of 'status' box
		'wStatusView',		# list view
		
		'wAdd',				# (QPushButton) svn add
		'wDelete',			# (QPushButton) svn delete
		
		'wRevert',			# (QPushButton) svn revert
		
		'wCreatePatch',		# (QPushButton) create patch (i.e. svn diff)
		
		'wCommit',			# (QPushButton) svn commit - to main branch
	);
	
	# Setup ================================================================
	
	# ctor
	def __init__(self, branchType):
		super(BranchPane, self).__init__();
		
		# setup internal settings
		self.branchType = branchType;
		
		# setup layout manager
		self.layout = QVBoxLayout();
		self.setLayout(self.layout);
		
		# init widgets
		self.setupUI();
		
	# main widget init
	def setupUI(self):
		# 1) url widget
		self.wUrl = LabelledTextWidget("URL", "https://svnroot/my-branch", 
			"URL pointing to where the branch is stored in the SVN repository");
		self.layout.addWidget(self.wUrl);
		
		# space ................
		self.layout.addSpacing(15);
		
		# 2) "update" group
		gbox = QGridLayout();
		gbox.setSpacing(0);
		self.layout.addLayout(gbox);
		
		# 2a) update from repository 
		self.wUpdate = QPushButton("SVN Update");
		self.wUpdate.clicked.connect(self.svnUpdate);
		gbox.addWidget(self.wUpdate, 1,1); # r1 c1
		
		# 2b) apply patch
		self.wApplyPatch = QPushButton("Apply Patch");
		self.wApplyPatch.clicked.connect(self.svnApplyPatch);
		gbox.addWidget(self.wApplyPatch, 2,1); # r2 c1
		
		# space ................
		self.layout.addSpacing(15);
		
		# 3) "status" group
		gbox = QGridLayout();
		self.layout.addLayout(gbox);
		
		# 3.1a) "status" label
		gbox.addWidget(QLabel("Status:"), 1,1); # r1 c1
		
		# 3.1b) "refresh" button
		# FIXME: need icons...
		self.wRefreshStatus = QPushButton(QIcon.fromTheme("view-refresh"), "Refresh"); 
		self.wRefreshStatus.clicked.connect(self.svnRefreshStatus);
		gbox.addWidget(self.wRefreshStatus, 1,3); # r1 c3
		
		# 3.2) status list
		self.wStatusView = SvnStatusList();
		gbox.addWidget(self.wStatusView, 2,1, 1,3); # r2 c1, h1,w3
		
		# ...................
		
		# 4) "add/delete" group
		gbox = QGridLayout();
		gbox.setSpacing(0);
		self.layout.addLayout(gbox);
		
		# 4a) add
		self.wAdd = QPushButton("Add");
		self.wAdd.clicked.connect(self.svnAdd);
		gbox.addWidget(self.wAdd, 1,1); # r1 c1
		
		# 4b) delete
		self.wDelete = QPushButton("Delete");
		self.wDelete.clicked.connect(self.svnDelete);
		gbox.addWidget(self.wDelete, 1,2); # r1 c2
		
		# ...................
		
		# 5) Revert
		self.wRevert = QPushButton("Revert");
		self.wRevert.clicked.connect(self.svnRevert);
		self.layout.addWidget(self.wRevert);
		
		# ...................
		
		# 6) "Commit" group
		gbox = QGridLayout();
		gbox.setSpacing(0);
		self.layout.addLayout(gbox);
		
		# 6a) Create Patch
		self.wCreatePatch = QPushButton("Create Patch");
		self.wCreatePatch.clicked.connect(self.svnCreatePatch);
		gbox.addWidget(self.wCreatePatch, 1,1); # r1 c1
		
		# 6b) Commit
		if self.branchType == BranchPane.TYPE_TRUNK_REF:
			self.wCommit = QPushButton("Reintegrate Branch Changes");
			self.wCommit.clicked.connect(self.svnReintegrate);
		else:
			self.wCommit = QPushButton("Commit");
			self.wCommit.clicked.connect(self.svnCommit);
		gbox.addWidget(self.wCommit, 2,1); # r2 c1
		
	# Callbacks ==============================================================
	
	# Placeholder ------------------------------------------------------------
	
	def unimplementedFeatureCb(self, feature):
		QMessageBox.warning(self,
			feature,
			"Feature not yet implemented")
	
	# Working Copy Import ----------------------------------------------------
	
	def svnUpdate(self):
		self.unimplementedFeatureCb("Update");
	
	def svnApplyPatch(self):
		self.unimplementedFeatureCb("Apply Patch");
	
	# Status List Ops ---------------------------------------------------------
	
	def svnRefreshStatus(self):
		self.unimplementedFeatureCb("Refresh Status");
	
	# Status List Dependent --------------------------------------------------
	
	# check if any entries in the list are checked
	# - helper for all status list dependent methods
	def statusListOkPoll(self):
		return True; # FIXME
	
	def svnAdd(self):
		self.unimplementedFeatureCb("Add");
		
	def svnDelete(self):
		self.unimplementedFeatureCb("Delete");
		
	def svnRevert(self):
		self.unimplementedFeatureCb("Revert");
	
	def svnCreatePatch(self):
		self.unimplementedFeatureCb("Create Patch");
		
	def svnCommit(self):
		# get list of files to change
		
		# create commit dialog 
		dlg = SvnCommitDialog(self);
		
		# process user response, and commit if allowed
		reply = dlg.exec_();
		
		if reply == QDialog.Accepted:
			# retrieve log message
			# FIXME: temp testing code...
			print "Log message obtained:"
			print dlg.getLogMessage();
			print "Proceeding to commit!"
			
			# bring up svn action dialog, and perform actual commit
			dlg2 = SvnOperationDialog(self, "Commit");
			dlg2.exec_();
		else:
			print "Commit cancelled..."
		
	def svnReintegrate(self):
		# this is destructive, so must ask for confirmation in case of error
		reply = QMessageBox.question(self, 'Commit',
			"Are you sure you want to reintegrate changes from branch back to trunk?", 
			QMessageBox.Yes | QMessageBox.No, 
			QMessageBox.No);
		
		# only if user is self-aware, we can go ahead
		if reply == QMessageBox.Yes:
			self.svnCommit();
		else:
			print "Cancelled reintegrate..."
 

# -----------------------------------------
# Main Window

# Main Window
class DualityWindow(QWidget):
	# Class Defines ==================================
	
	# Instance Vars ==================================
	
	__slots__ = (
		'wDirectory',
		'wTabs',
		
		'branchTabs',
	);
	
	# Setup ========================================== 
	
	# ctor
	def __init__(self, parent=None):
		# toplevel 'widget' (i.e. window) - no parent
		QWidget.__init__(self, parent);
		
		# main window settings
		self.setWindowTitle('Duality SVN')
		#self.setGeometry(150, 150, 400, 500)
		
		# contents
		self.setupUI();
	
	# main widget init
	def setupUI(self):
		# main layout container
		mainVBox = QVBoxLayout();
		self.setLayout(mainVBox);
		
		# 1) directory panel
		self.wDirectory = LabelledTextWidget("W/C Directory", "src/", "Directory where working copy is located");
		mainVBox.addWidget(self.wDirectory);
		
		# 2) tab panel
		self.wTabs = QTabWidget();
		mainVBox.addWidget(self.wTabs);
		
		# 2a) first branch
		self.pBranch1 = BranchPane(BranchPane.TYPE_TRUNK);
		self.wTabs.addTab(self.pBranch1, "Trunk");

# -----------------------------------------
	
app = QApplication(sys.argv)

mainWin = DualityWindow()
mainWin.show()

sys.exit(app.exec_())

###########################################
