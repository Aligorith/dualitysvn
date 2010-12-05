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
import subprocess

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
	#status("Setting up Working Copy Duality...")
	duplicateSvnMetadata(srcdir);
	
	# perform an "svn copy" operation to make a new branch on the repository
	# 	WC + URL = instant commit 
	#status("Branching Commit Pending...");
	cmd = 'svn co "%(sd)s" %(tar)s -m "%(cm)s"' % {'sd':srcdir, 'tar':target, 'cm':"Creating '%s' branch"%(branchName)}
	OSU_runCommand(cmd); 
	
	# change working copy to the branch now
	#status("Switching Working Copy to New Branch...");
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
class SvnStatusListItem:
	# Class Defines ======================================
	# File Status
	FileStatusMap = {
		' ':"Unchanged",
		'A':"Added",
		'C':"Conflicted",
		'D':"Deleted",
		'I':"Ignored",
		'M':"Modified",
		'R':"Replaced",
		'X':"External",
		'?':"Unversioned",
		'!':"Missing",
		'~':"Obstructed" #versioned item obstructed by some item of a different kind
	}
	
	# Property Status
	PropStatusMap = {
		' ':"Unchanged",
		'C':"Conflicted",
		'M':"Modified"
	}
	
	# Setup ==============================================
	
	# ctor
	# < (initStr): (str) optional string to parse to get relevant info
	def __init__(self, initStr=None):
		# init placeholders
		self.defaultEnabled = True;
		
		self.path = "";
		
		self.file_status = SvnStatusListItem.FileStatusMap[' '];
		self.prop_status = SvnStatusListItem.PropStatusMap[' '];
		
		# initialise from string
		if initStr:
			self.fromString(initStr);
			
	# parse settings from a string
	# < initStr: (str) input string
	def fromString(self, initStr):
		try:
			# chop into 2 parts: status and path
			statusStr = initStr[:7]; # first 7 columns 
			self.path = initStr[8:]; # rest of string after status columns
			
			# decipher status string
				# col 1: file status
			self.file_status = SvnStatusListItem.FileStatusMap[statusStr[0]];
				# col 2: property status
			self.prop_status = SvnStatusListItem.PropStatusMap[statusStr[1]];
			
			# modify enabled status from placeholder
			self.setAutoDefaultEnabledStatus();
		except:
			pass;
			
	# Enabled Status ===========================================
	
	# automatically determine whether "default enabled" status is on
	def setAutoDefaultEnabledStatus(self):
		# disable based on file status, so check on each of the bad ones...
		badKeys = (' ', 'C', 'I', 'X', '?', '!');
		
		for k in badKeys:	
			if self.file_status == SvnStatusListItem.FileStatusMap[k]:
				self.defaultEnabled = False;
				break;
		else:
			# by default (i.e. if nothing caught), this is on
			self.defaultEnabled = True;

# ......................

# Qt wrapper for SvnStatusListItem, which represents one "row" in the list
# TODO: implement support for hiding some items temporarily...
class SvnStatusListItemModel(QAbstractItemModel):
	# Class Defines =========================================
	# Header labels
	HeaderLabels = ("Path", "Status", "Prop Status");
	
	# Setup =================================================
	# ctor
	# < listItems: (list<SvnStatusListItem>) list of SvnStatusListItem's
	def __init__(self, listItems=None, parent=None):
		super(SvnStatusListItemModel, self).__init__(parent);
		
		# store reference to the list of data being shown
		if listItems:
			self.listItems = listItems;
		else:
			self.listItems = [];
		self.checked = [];
	
	# Methods ===============================================
	
	# add entry
	def add(self, item):
		# warn everybody to update
		idx = len(self.listItems); # always as last index of list
		self.beginInsertRows(QModelIndex(), idx, idx);
		
		# add to list
		self.listItems.append(item);
		
		# if "defaultEnabled", add to checked list
		if item.defaultEnabled:
			self.checked.append(item);
		
		# done updating
		self.endInsertRows();
		
	# clear all entries
	def clearAll(self):
		# just do a remove of all
		totLen = len(self.listItems);
		self.beginRemoveRows(QModelIndex(), 0, totLen);
		
		# clear lists
		self.listItems = [];
		self.checked = [];
		
		# done
		self.endRemoveRows();
	
	# QAbstractItemMode implementation ======================
	
	# return the relevant data for each column's header cell
	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			# section = header name
			return QVariant(SvnStatusListItemModel.HeaderLabels[section]);
		
		return None;
		
	# total number of attributes - static
	def columnCount(self, parent):
		# columns represent different attributes per record
		return len(SvnStatusListItemModel.HeaderLabels);
		
	# total number of records - dynamic
	def rowCount(self, parent):
		# each row represents 1 record
		return len(self.listItems);
	
	# return parent index of item - nothing has parents here!
	def parent(self, index):
		# no item is a child of anything
		return QModelIndex();
		
	# get QModelIndex for row/column combination?
	# < row: (int) row number - 0 indexed
	# < col: (int) column number - 0 indexed
	# < (parent): (QModelIndex) unused...
	def index(self, row, col, parent):
		# must be within bounds
		if not self.hasIndex(row, col, parent):
			return QModelIndex();
			
		# create model-index wrapper for this cell
		return self.createIndex(row, col, self.listItems[row]); # last arg err...
	
	# get QtCore.Qt.ItemFlags
	def flags(self, index):
		if not index.isValid():
			return QtCore.Qt.NoItemFlags
		
		# items can be selected + checked
		return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable;
	
	# get data for model cell
	# < index: (QModelIndex) row/column reference for cell to get data for
	# < role: (QtCore.Qt.ItemDataRole/int) which aspect of cell to get data for
	# > return[0]: (QVariant) relevant data, wrapped in "QVariant" wrapper (i.e. "anything goes container")
	def data(self, index, role):
		# valid indices only
		if not index.isValid():
			return None;
		
		# get item
		item = self.listItems[index.row()];
		
		# what data to return
		if role == Qt.DisplayRole:
			# display data - depends on the index
			if index.column() == 2:
				# property status
				return QVariant(item.prop_status);
			elif index.column() == 1:
				# status
				return QVariant(item.file_status);
			else:
				# path
				return QVariant(item.path);
		elif role == Qt.ToolTipRole:
			# tooltip - for path only
			if index.column() == 0:
				# TODO: have a specially formatted string with other stuff too?
				return QVariant(item.path);
			else:
				# other columns have no data for now
				return None;
		elif role == Qt.CheckStateRole:
			# checkable - for first column only
			if index.column() == 0:
				return Qt.Checked if item in self.checked else Qt.Unchecked;
			else:
				return None;
		else:
			# other roles not supported...
			return None;
	
	# set data for model cell
	# < index: (QModelIndex) cell reference
	# < value: (QVariant) wrapper for data stored
	# < role: (QtCore.Qt.ItemDataRole/int) should usually be edit only...
	def setData(self, index, value, role = Qt.EditRole):
		if index.isValid():
			# get item
			item = self.listItems[index.row()];
			
			# only checkboxes are editable...
			if (index.column() == 0) and (role == Qt.CheckStateRole):
				if (value == Qt.Checked):
					self.checked.append(item);
					return True;
				else:
					self.checked.remove(item);
					return True;
		
		# nothing done
		return False;
	
	# sort the data 
	# < col: (int) column to sort by
	# < order: (QtCore.Qt.SortOrder/int) order to sort entries in
	def sort(self, col, order = Qt.AscendingOrder):
		# column index defines the key function used
		keyFuncs = (
			lambda x: x.path,
			lambda x: x.file_status,
			lambda x: x.prop_status
		);
		
		# perform a reverse-order sort?
		rev = (order == Qt.DescendingOrder);
		
		# sort the internal list
		self.listItems = sorted(self.listItems, key=keyFuncs[col], reverse=rev); 

# ......................

# Show "status" of files/directories within working copy,
# allowing some to be included/excluded from SVN operations
class SvnStatusList(QTreeView):
	# Setup =============================================
	
	# ctor
	# < fileList: (list<SvnStatusListItem>) list of items to populate model with
	def __init__(self, fileList=None):
		super(SvnStatusList, self).__init__();
		
		# view setup settings
		self.setRootIsDecorated(False);
		self.setAlternatingRowColors(True);
		self.setUniformRowHeights(True);
		
		# allow sorting - by the file status by default
		self.setSortingEnabled(True);
		self.sortByColumn(1, Qt.AscendingOrder);
		
		# create model
		self.model = SvnStatusListItemModel(fileList);
		self.setModel(self.model);
		
		# tweak column extents - only first column should stretch
		self.header().setStretchLastSection(False);
		#self.header().setResizeMode(0, QHeaderView.Stretch);
		
	# Methods ===========================================
	
	# Refresh the status list - hook for UI command
	# < wcDir: (str) working copy directory
	def refreshList(self, wcDir):
		print "Refreshing..."
		
		# clear lists first
		self.model.clearAll();
		
		# run svn status operation
		# TODO: it might be better for performance to use QProcess to gradually update stuff...
		args = ["svn", "--non-interactive", "--ignore-externals", "status"];
		p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=wcDir);
		
		for line in p.stdout:
			# strip off newline character first
			line = line.rstrip("\n");
			
			# process line
			if len(line):
				# parse the output to create a new line
				item = SvnStatusListItem(line);
				print "created new item - %s, %s, '%s' - from '%s'" % (item.file_status, item.prop_status, item.path, line);
				self.model.add(item);
				
		# hack: force sorting to be performed again now
		self.setSortingEnabled(True);
		
	# Get list of selected items to operate on
	def getOperationList(self):
		# just return a copy of the model's list...
		return self.model.checked[:];

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
		
		# default global args for process first
		self.args = ['--non-interactive']; 
		
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
	# < parent: (QWidget) window that owns this dialog
	# < (branchName): (str) string representing the name or URL of the branch changes are getting committed to
	# < (filesList): (list<SvnStatusListItem>) list of files that will be involved in the commit
	def __init__(self, parent, branchName, filesList):
		super(SvnCommitDialog, self).__init__(parent);
		
		# toplevel stuff
		self.setWindowTitle("Log Message for Commit - Duality SVN");
		self.setGeometry(150, 150, 600, 400);
		
		# setup UI
		self.layout = QVBoxLayout();
		self.setLayout(self.layout);
		
		self.setupUI(branchName, filesList);
		
	# main widget init
	def setupUI(self, branchName, filesList):
		# 1) "staged" files
		gb = QGroupBox("Changes Pending");
		self.layout.addWidget(gb);
		
		grp = QVBoxLayout();
		gb.setLayout(grp);
		
		# 1a) branch target
		grp.addWidget(QLabel("For: " + branchName));
		
		# 2a) list of files - not editable
		# FIXME: maybe we just need another status list!
		self.wFileList = SvnStatusList(filesList);
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
		self.updateActionWidgets();
		
	# main widget init
	def setupUI(self):
		# 1) url widget
		gbox = QGridLayout();
		self.layout.addLayout(gbox);
		
		# 1.1) url label
		gbox.addWidget(QLabel("URL:"), 1,1); # r1 c1
		
		# 1.2) directory field
		# TODO: perhaps this shouldn't be editable at all!
		self.wUrl = QLineEdit("https://svnroot/my-branch");
		self.wUrl.setToolTip("URL pointing to where the branch is stored in the SVN repository");
		
		gbox.addWidget(self.wUrl, 1,2); # r1 c2
		
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
		self.wStatusView.clicked.connect(self.updateActionWidgets);
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
		# call refresh on list
		srcDir = r"c:\blenderdev\b250\blender" # FIXME: hook up to proper field
		self.wStatusView.refreshList(srcDir);
		
		# update widgets...
		self.updateActionWidgets();
		
	# update action widgets in response to svn status list changes
	def updateActionWidgets(self):
		# get selection list from status list
		files = self.statusListGetOperatable();
		
		# for now, enable or disable only based on whether there's anything in list
		if len(files):
			# enabled
			self.wAdd.setEnabled(True);
			self.wDelete.setEnabled(True);
			self.wRevert.setEnabled(True);
			self.wCreatePatch.setEnabled(True);
			self.wCommit.setEnabled(True);
		else:
			# disabled
			self.wAdd.setEnabled(False);
			self.wDelete.setEnabled(False);
			self.wRevert.setEnabled(False);
			self.wCreatePatch.setEnabled(False);
			self.wCommit.setEnabled(False);
	
	
	# Status List Dependent --------------------------------------------------
	
	# error for nothing selected
	def noDataSelectedCb(self, feature):
		QMessageBox.warning(self,
			feature+" Error",
			"No paths selected for %s operation.\nEnable some of the checkboxes beside paths in the Status list and try again." % (feature))
	
	# get list of items to operate on
	def statusListGetOperatable(self):
		return self.wStatusView.getOperationList();
	
	# ...........
	
	def svnAdd(self):
		# get list of files to change
		files = self.statusListGetOperatable();
		if len(files) == 0:
			self.noDataSelectedCb("Add");
			return;
		
		self.unimplementedFeatureCb("Add");
		
	def svnDelete(self):
		# get list of files to change
		files = self.statusListGetOperatable();
		if len(files) == 0:
			self.noDataSelectedCb("Delete");
			return;
		
		self.unimplementedFeatureCb("Delete");
		
	def svnRevert(self):
		# get list of files to change
		files = self.statusListGetOperatable();
		if len(files) == 0:
			self.noDataSelectedCb("Revert");
			return;
		
		self.unimplementedFeatureCb("Revert");
	
	def svnCreatePatch(self):
		# get list of files to change
		files = self.statusListGetOperatable();
		if len(files) == 0:
			self.noDataSelectedCb("Create Patch");
			return;
		
		self.unimplementedFeatureCb("Create Patch");
		
	def svnCommit(self):
		# get list of files to change
		files = self.statusListGetOperatable();
		if len(files) == 0:
			self.noDataSelectedCb("Commit");
			return;
		
		# create commit dialog 
		branchName = "<branchName>" # FIXME
		dlg = SvnCommitDialog(self, branchName, files);
		
		# process user response, and commit if allowed
		reply = dlg.exec_();
		
		if reply == QDialog.Accepted:
			# retrieve log message
			# FIXME: temp testing code...
			print "Log message obtained:"
			print dlg.getLogMessage(); # FIXME: make convert this to save file op...
			print "Proceeding to commit!"
			
			# bring up svn action dialog, and perform actual commit
			dlg2 = SvnOperationDialog(self, "Commit");
			# TODO: setup commands for commit action
			
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
		'layout',
		
		'wDirectory',
		'wDirBrowseBut',
		
		'wTabs',
		
		'branchTabs',
	);
	
	# Setup ========================================== 
	
	# ctor
	def __init__(self, parent=None):
		# toplevel 'widget' (i.e. window) - no parent
		QWidget.__init__(self, parent);
		
		# main window settings
		self.setWindowTitle('Duality SVN');
		
		# contents
		self.setupUI();
	
	# main widget init
	def setupUI(self):
		# main layout container
		self.layout = QVBoxLayout();
		self.setLayout(self.layout);
		
		# 1) working copy panel
		self.setupWorkingCopyPanel();
		
		# ..........
		
		# 2) tab panel
		self.wTabs = QTabWidget();
		self.layout.addWidget(self.wTabs);
		
		# 2a) first branch
		self.pBranch1 = BranchPane(BranchPane.TYPE_TRUNK);
		self.wTabs.addTab(self.pBranch1, "Trunk");
		
	# setup working copy panel
	def setupWorkingCopyPanel(self):
		# 0) group box
		gb = QGroupBox("Working Copy");
		self.layout.addWidget(gb);
		
		vbox = QVBoxLayout();
		gb.setLayout(vbox);
		
		# ...........
		
		# 1) "directory"
		gbox = QGridLayout();
		vbox.addLayout(gbox);
		
		# 1.1) directory label
		gbox.addWidget(QLabel("Directory:"), 1,1); # r1 c1
		
		# 1.2) directory field
		self.wDirectory = QLineEdit("src/");
		self.wDirectory.setToolTip("Directory where working copy is located");
		
		gbox.addWidget(self.wDirectory, 1,2); # r1 c2
		
		# 1.2) browse-button for directory widget
		self.wDirBrowseBut = QPushButton("..."); # FIXME: too wide
		self.wDirBrowseBut.clicked.connect(self.dirBrowseCb);
		
		gbox.addWidget(self.wDirBrowseBut, 1,3); # r1 c3

	# Callbacks ========================================== 
	
	# Working copy directory browse callback
	def dirBrowseCb(self):
		# get new directory
		newDir = QFileDialog.getExistingDirectory(self, "Open Directory",
			"/",
			QFileDialog.ShowDirsOnly
			| QFileDialog.DontResolveSymlinks);
		
		# set this directory
		if newDir:
			self.wDirectory.setText(newDir);

# -----------------------------------------
	
app = QApplication(sys.argv)

mainWin = DualityWindow()
mainWin.show()

sys.exit(app.exec_())

###########################################
