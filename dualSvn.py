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

###########################################
# Settings Container

import ConfigParser

class DualitySettings:
	# Class Defines ===============================
	# default filename
	DEFAULT_FILENAME = "branchConfig.duality";
	
	# Instance Vars ===============================
	__slots__ = (
		'fileN',			# (str) name of file to use
		
		'autofile',			# (bool) whether this is an "automatically generated" filename
		'unsaved',			# (bool) are there unsaved changes?
		
		'workingCopyDir',	# (str) directory of working copy
		
		'urlTrunk',			# (str) url of "trunk"
		#'nameTrunk',		# (str) user-assigned name for "trunk"
		
		'urlBranch',		# (str) url of "branch"
		#'nameBranch', 	# (str) user-assigned name for "branch"
	);
	
	# Setup =====================================
	
	# ctor
	# < (fileN): (str) optional name of file where settings are stored (as per first arg)
	#			otherwise, derive from default name + current directory
	def __init__(self, fileN=None):
		# set default values first
		self.resetDefaults();
		
		# make sure we have a workable file, even if this is newly added
		self.verifyLoadFile(fileN, True);
		
	# Config I/O =================================
	
	# Verify filename
	# < fileN: (str) name of file
	# < (addIfInvalid): (bool) if the provided filename is invalid or null, create default filename
	# > return[0]: (bool) whether a filename has been successfully set
	def verifyLoadFile(self, fileN, addIfInvalid=False):
		# validate provided string (if available), falling back on the default string
		if fileN:
			if os.path.exists(fileN):
				# save filename and try to load stored settings
				self.fileN = fileN;
				self.load();
			else:
				# nullify and fall back on next step...
				fileN = None;
		
		# create default filename otherwise...
		if (fileN is None) and (addIfInvalid):
			# find current directory 
			# - this is where the config file will be dumped
			# - we capture it now, in case this changes due to later ops
			cwd = os.getcwd();
			
			# make and store
			fileN = os.path.join(cwd, DualitySettings.DEFAULT_FILENAME);
			self.fileN = fileN;
			
			# this is an 'automatically generated file' (which doesn't actually exist on disk yet!)
			self.autofile = True;
		
		# return whether we now have a valid filename
		return (fileN is not None);
		
	# Reset settings to default values
	def resetDefaults(self):
		# autofile cannot be on, if we're loading in real files after calling this...
		self.autofile = False;
		
		# default = no changes :)
		self.unsaved = False;
		
		# "src" dir living beside the project file
		self.workingCopyDir = "./src";		
		
		# example url - represents most common situations...
		self.urlTrunk = "https://svnroot/project/trunk";
		
		# no branches by default!
		self.urlBranch = None; 
		
	# -----------------------
	
	# Load config file
	def load(self):
		# reset defaults
		self.resetDefaults();
		
		# grab filepointer
		with open(self.fileN, 'r') as f:
			# create parser, and read in the file
			cfg = ConfigParser.SafeConfigParser();
			cfg.readfp(f);
			
			# grab the values for the various parts
			self.workingCopyDir = cfg.get("Project", "WorkingCopy");
			
			self.urlTrunk = cfg.get("Trunk", "url");
			
			if cfg.has_section("Branch"):
				self.urlBranch = cfg.get("Branch", "url");
			
	# Save config file
	def save(self):
		# create parser
		cfg = ConfigParser.SafeConfigParser();
		
		# load in the settings
		cfg.add_section("Project");
		cfg.set("Project", "WorkingCopy", self.workingCopyDir);
		
		cfg.add_section("Trunk");
		cfg.set("Trunk", "url", self.urlTrunk);
		
		if self.urlBranch:
			cfg.add_section("Branch");
			cfg.set("Branch", "url", self.urlBranch);
			
		# write settings to file
		with open(self.fileN, 'wb') as cfgFile:
			cfg.write(cfgFile);
			
		# clear unsaved changes flag
		self.unsaved = False;
		
	# Setters =================================
	# Note: these setters MUST be used, otherwise, we don't get the the unsaved tag being set (causing problems later)
	
	# < value: (str) new value
	def setWorkingCopyDir(self, value):
		self.workingCopyDir = value;
		self.unsaved = True;
		
	# < value: (str) new value
	def setUrlTrunk(self, value):
		self.urlTrunk = value;
		self.unsaved = True;
		
	# < value: (str) new value
	def setUrlBranch(self, value):
		self.urlBranch = value;
		self.unsaved = True;
	

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
	# < (listItems): (list<SvnStatusListItem>) list of SvnStatusListItem's for populating as a filtered copy of another instance.
	#	! Checkboxes will not be available when such a list is supplied, as further editing isn't needed.
	def __init__(self, listItems=None, parent=None):
		super(SvnStatusListItemModel, self).__init__(parent);
		
		# store reference to the list of data being shown
		if listItems:
			self.listItems = listItems;
		else:
			self.listItems = [];
		self.checked = [];
		
		# checkboxes will only be shown if we're not being supplied with
		# a list to simply display again (in another place)
		self.checksOn = (listItems is None);
	
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
		
	# toggle select/deselect all
	def toggleAllChecked(self):
		self.beginResetModel();
		
		if len(self.checked):
			# deselect all
			self.checked = [];
		else:
			# select all
			self.checked = self.listItems[:];
			
		self.endResetModel();
	
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
		
		# at very least, items can be selected
		flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable;
		
		# if we can show checkboxes, include that too
		if self.checksOn:
			flags |= Qt.ItemIsUserCheckable;
		
		return flags;
	
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
		elif role == Qt.ForegroundRole:
			# text color
			if index.column() == 1:
				# status of file = color
				colorMap = {
					' ':QColor(Qt.lightGray),
					'A':QColor(Qt.darkCyan),
					'C':QColor(Qt.red),
					'D':QColor(Qt.darkMagenta),
					'I':QColor(Qt.darkYellow),
					'M':QColor(Qt.blue),
					'R':QColor(Qt.darkCyan),
					'X':QColor(Qt.yellow),
					'?':QColor(Qt.gray),
					'!':QColor(Qt.darkRed),
					'~':QColor(Qt.darkRed) #versioned item obstructed by some item of a different kind
				}
				
				# find the right one that matches for this item
				for shortKey,longKey in SvnStatusListItem.FileStatusMap.iteritems():
					if longKey == item.file_status:
						return colorMap[shortKey];
				else:
					# no appropriate decoration found
					return None;
			else:
				return None;
		elif role == Qt.ToolTipRole:
			# construct tooltip for all entries
			tooltipTemplate = "\n".join([
				"<b>Path:</b> %s",
				"<b>File Status:</b> %s",
				"<b>Property Status:</b> %s"]);
			
			return QVariant(tooltipTemplate % (item.path, item.file_status, item.prop_status));
		elif (role == Qt.CheckStateRole) and (self.checksOn):
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
			if (index.column() == 0) and (role == Qt.CheckStateRole) and (self.checksOn):
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
		
		# prevent crashes on double-clicking
		self.setExpandsOnDoubleClick(False);
		
		# allow sorting - by the file status by default
		self.setSortingEnabled(True);
		self.sortByColumn(1, Qt.AscendingOrder);
		
		# create model
		self.model = SvnStatusListItemModel(fileList);
		self.setModel(self.model);
		
		# tweak column extents - only first column should stretch
		self.header().setStretchLastSection(False);
		
		#self.header().setResizeMode(0, QHeaderView.Stretch); # <--- enables nice layout
		#self.header().setResizeMode(0, QHeaderView.Interactive); # <--- needed for user tweaking though!
		
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
# TODO: allow queuing up multiple operations for the same dialog?
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
		self.setGeometry(150, 150, 600, 300);
		
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
		#self.wStatus = SvnOperationList(); # FIXME: restore this when it's completed
		self.wStatus = QPlainTextEdit("");
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
		self.connect(self.process, SIGNAL("finished(int, QProcess::ExitStatus)"), self.pEnded);
		
	# Methods ==========================================
	
	# External Setup API ------------------------------
	
	# Set the svn operation that needs to be performed
	# < svnOpName: (str) name of the operation (i.e. commit,up,etc.) to perform using svn
	def setOp(self, svnOpName):
		self.svnOp = svnOpName;
	
	# Add a list of arguments to be passed to svn when running it
	# args: (list<str>) list of arguments to run
	def addArgs(self, args):
		self.args += args;
		
	# Setup process environment, modifying only the aspects that are non-null
	# < wdir: (str) working directory to execute commands in
	def setupEnv(self, branchType):
		# working directory?
		self.process.setWorkingDirectory(project.workingCopyDir);
		
		# ...............
		
		# setup process environment
		env = QProcessEnvironment.systemEnvironment();
		self.process.setProcessEnvironment(env); # assume that we can set this first
		
		# standard or secondary branch?
		# only use "_svn" set when this is "reference" trunk (i.e. working copy belongs to 2 masters now)
		# TODO: move this define up somewhere else?
		useSecondaryBranch = (branchType == BranchPane.TYPE_TRUNK_REF); 
		
		if useSecondaryBranch:
			env.insert(SVN_HACK_ENVVAR, "1");
		
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
		self.process.start("svn", [self.svnOp]+self.args);
		
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
		#self.wStatus.appendFromStr(line); # TMP for later...
		self.wStatus.appendPlainText(line);
	
	def readErrors(self):
		# switch to stderr channel to read, then switch back
		self.process.setReadChannel(QProcess.StandardError);
		
		line = str(self.process.readLine()).rstrip("\n");
		self.wStatus.appendPlainText("<ERROR>: " + line);
		
		self.process.setReadChannel(QProcess.StandardOutput);
		
	# Buttons ------------------------------------------
	
	# callback called when cancelling dialog
	def reject(self):
		# end the process first
		self.endProcess();
		# TODO: feedback on whether this succeeded
		
		# now, cancel the dialog using it's own version
		super(SvnOperationDialog, self).reject();
	
	# callback called when svn operation process ends
	def pEnded(self, exitCode, exitStatus):
		# grab 3 more lines - to grab the last bits of info (status info)
		self.readOutput();
		self.readOutput();
		self.readOutput();
		
		# if exited with some problem, make sure we warn
		# TODO: set own status codes...?
		if exitStatus == QProcess.CrashExit:
			QMessageBox.warning(self,
				"SVN Error",
				"%s operation was not completed successfully" % (self.opName));
			self.status = SvnOperationDialog.STATUS_FAILED;
		else:
			self.status = SvnOperationDialog.STATUS_DONE;
		
		# enable the "done" button now, and disable cancel (not much we can do)
		self.wOk.setEnabled(True);
		self.setName();
	
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	
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
				lines = SvnCommitDialog.wordWrapper.wrap(paragraph);
				for line in lines:
					f.write("%s\n" % line);
			
			# finish up
			f.close();
		
		# return full path name
		# FIXME: the directory where this gets dumped should be user defined
		return os.path.join(os.getcwd(), fileN);

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
		self.wUrl = QLineEdit("https://svnroot/my-branch");
		self.wUrl.setReadOnly(True); # XXX: should not be editable, but we need to grab this from somewhere...
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
		self.wUpdate.setToolTip("Fetch and apply recent changes made to the repository to working copy");
		self.wUpdate.clicked.connect(self.svnUpdate);
		
		gbox.addWidget(self.wUpdate, 1,1); # r1 c1
		
		# 2b) apply patch
		self.wApplyPatch = QPushButton("Apply Patch");
		self.wApplyPatch.setToolTip("Apply changes described in patch file to working copy");
		self.wApplyPatch.clicked.connect(self.svnApplyPatch);
		
		gbox.addWidget(self.wApplyPatch, 2,1); # r2 c1
		
		# space ................
		self.layout.addSpacing(15);
		
		# 3) "status" group
		gbox = QGridLayout();
		self.layout.addLayout(gbox);
		
		# 3.1a) "status" label
		gbox.addWidget(QLabel("Status:"), 1,1); # r1 c1
		
		# 3.1b) "toggle all" button
		self.wToggleAllStatus = QPushButton("Toggle All");
		self.wToggleAllStatus.setToolTip("Toggle whether all or none or the paths are included for editing (shown by checked status)");
		self.wToggleAllStatus.clicked.connect(self.statusToggleAll);
		
		gbox.addWidget(self.wToggleAllStatus, 1,3); # r1 c3
		
		# 3.1c) "refresh" button
		# FIXME: need icons...
		self.wRefreshStatus = QPushButton(QIcon.fromTheme("view-refresh"), "Refresh"); 
		self.wRefreshStatus.setToolTip("Refresh the list of paths shown in the list and their current versioning status");
		self.wRefreshStatus.clicked.connect(self.svnRefreshStatus);
		
		gbox.addWidget(self.wRefreshStatus, 1,4); # r1 c4
		
		# 3.2) status list
		self.wStatusView = SvnStatusList();
		self.wStatusView.clicked.connect(self.updateActionWidgets);
		gbox.addWidget(self.wStatusView, 2,1, 1,4); # r2 c1, h1,w4
		
		# ...................
		
		# 4) "add/delete" group
		gbox = QGridLayout();
		gbox.setSpacing(0);
		self.layout.addLayout(gbox);
		
		# 4a) add
		self.wAdd = QPushButton("Add");
		self.wAdd.setToolTip("Mark selected paths for addition to repository during a future commit");
		self.wAdd.clicked.connect(self.svnAdd);
		
		gbox.addWidget(self.wAdd, 1,1); # r1 c1
		
		# 4b) delete
		self.wDelete = QPushButton("Delete");
		self.wDelete.setToolTip("Mark selected paths for deletion during a future commit");
		self.wDelete.clicked.connect(self.svnDelete);
		
		gbox.addWidget(self.wDelete, 1,2); # r1 c2
		
		# ...................
		
		# 5) Revert
		self.wRevert = QPushButton("Revert");
		self.wRevert.setToolTip("Undo changes to selected paths made in local copy");
		self.wRevert.clicked.connect(self.svnRevert);
		
		self.layout.addWidget(self.wRevert);
		
		# ...................
		
		# 6) "Commit" group
		gbox = QGridLayout();
		gbox.setSpacing(0);
		self.layout.addLayout(gbox);
		
		# 6a) Create Patch
		self.wCreatePatch = QPushButton("Create Patch");
		self.wCreatePatch.setToolTip("Create a file containing a summary of the changes made to the selected paths");
		self.wCreatePatch.clicked.connect(self.svnCreatePatch);
		
		gbox.addWidget(self.wCreatePatch, 1,1); # r1 c1
		
		# 6b) Commit
		if self.branchType == BranchPane.TYPE_TRUNK_REF:
			self.wCommit = QPushButton("Reintegrate Branch Changes");
			self.wCommit.setToolTip("Apply all changes made in branch back to trunk (from which it was originally branched from)");
			self.wCommit.clicked.connect(self.svnReintegrate);
		else:
			self.wCommit = QPushButton("Commit");
			self.wCommit.setToolTip("Send selected changes in working copy to repository");
			self.wCommit.clicked.connect(self.svnCommit);
		gbox.addWidget(self.wCommit, 2,1); # r2 c1
		
	# Callbacks ==============================================================
	
	# Placeholder ------------------------------------------------------------
	
	def unimplementedFeatureCb(self, feature):
		QMessageBox.warning(self,
			feature,
			"Feature not yet implemented")
	
	# Project Updates -------------------------------------------------------
	
	# update all widgets associated with project
	def updateProjectWidgets(self):
		# update url, and set editability status (only editable for standard trunk)
		if self.branchType == BranchPane.TYPE_BRANCH:
			self.wUrl.setText(project.urlBranch);
			self.wUrl.setReadOnly(True);
		elif self.branchType == BranchPane.TYPE_TRUNK_REF:
			self.wUrl.setText(project.urlTrunk);
			self.wUrl.setReadOnly(True);
		else:
			self.wUrl.setText(project.urlTrunk);
			self.wUrl.setReadOnly(False);
		
		# clear status list
		self.wStatusView.model.clearAll(); # TODO: make this general?
		self.updateActionWidgets();
	
	# Working Copy Import ----------------------------------------------------
	
	def svnUpdate(self):
		# setup svn action dialog
		dlg = SvnOperationDialog(self, "Update");
		dlg.setupEnv(self.branchType);
		dlg.setOp("up");
		
		# setup arguments for svn
		dlg.addArgs(["--accept", "postpone"]); # conflict res should be manually handled by user afterwards?
		
		# let it run now
		dlg.go();
		dlg.exec_();
	
	def svnApplyPatch(self):
		self.unimplementedFeatureCb("Apply Patch");		
	
	# Status List Ops ---------------------------------------------------------
	
	# refresh status list
	def svnRefreshStatus(self):
		# call refresh on list
		self.wStatusView.refreshList(project.workingCopyDir);
		
		# update widgets...
		self.updateActionWidgets();
		
	# toggle selected items
	def statusToggleAll(self):
		# call toggle on list model
		# TODO: should status view provide a wrapper for this?
		self.wStatusView.model.toggleAllChecked();
		
		# update widgets
		self.updateActionWidgets();
		
	# update action widgets in response to svn status list changes
	def updateActionWidgets(self):
		# get selection list from status list
		files = self.statusListGetOperatable();
		
		# for now, enable or disable only based on whether there's anything in list
		# TODO: advanced selective polling based on filtering certain stati
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
			
		# toggle button should only be active if the status list is populated
		self.wToggleAllStatus.setEnabled(self.wStatusView.model.rowCount(None) != 0);
	
	
	# Status List Dependent --------------------------------------------------
	
	# error for nothing selected
	def noDataSelectedCb(self, feature):
		QMessageBox.warning(self,
			feature+" Error",
			"No paths selected for %s operation.\nEnable some of the checkboxes beside paths in the Status list and try again." % (feature))
	
	# ...........
	
	# TODO: abstract these functions to a special list type for these...
	
	# get list of items to operate on
	# > return: (list<SvnStatusListItem>)
	def statusListGetOperatable(self):
		return self.wStatusView.getOperationList();
		
	# save given list of items' paths to a file to pass to the svn operation
	# < files: (list<SvnStatusListItem>) list of files to perform operation on
	# > return[0]: (str) name of file where these paths were saved to
	def saveStatusListPathsFile(self, files):
		# open hardcoded path
		TARGETS_FILENAME = "duality_targets.oplist"; # FIXME: move out of this function
		
		# write (full) paths only to file
		# XXX: do we need full paths here?
		with open(TARGETS_FILENAME, 'w') as f:
			for item in files:
				f.write(item.path + '\n');
		
		# return the full filename
		# FIXME: the directory where this gets dumped should be user defined
		return os.path.join(os.getcwd(), TARGETS_FILENAME);
	
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
		
		# filter list of files to not include externals or unversioned
		# TODO...
		
		# dump names of files to commit to another temp file
		tarFile = self.saveStatusListPathsFile(files);
		
		# create commit dialog, and prepare it for work
		dlg = SvnOperationDialog(self, "Revert");
		dlg.setupEnv(self.branchType);
		dlg.setOp("revert");
		
		dlg.addArgs(['--targets', tarFile]); # list of files to revert
		
		# run dialog and perform operation
		dlg.go();
		dlg.exec_();
		
		# cleanup temp files
		os.remove(tarFile);
	
	def svnCreatePatch(self):
		# get list of files to change
		files = self.statusListGetOperatable();
		if len(files) == 0:
			self.noDataSelectedCb("Create Patch");
			return;
		
		self.unimplementedFeatureCb("Create Patch");
		
	# perform SVN Commit
	# TODO: 
	#	- have a special prepass which performs svn add for missing files...
	# 	- directory read/write permissions issues...
	def svnCommit(self):
		# get list of files to change
		files = self.statusListGetOperatable();
		if len(files) == 0:
			self.noDataSelectedCb("Commit");
			return;
		
		# create commit dialog
		dlg = SvnCommitDialog(self, self.wUrl.text(), files);
		
		# process user response, and commit if allowed
		reply = dlg.exec_();
		
		if reply == QDialog.Accepted:
			# retrieve log message, and save it to a temp file
			logFile = dlg.saveLogMessage();
			
			# dump names of files to commit to another temp file
			tarFile = self.saveStatusListPathsFile(files);
			
			# create commit dialog, and prepare it for work
			dlg2 = SvnOperationDialog(self, "Commit");
			dlg2.setupEnv(self.branchType);
			dlg2.setOp("commit");
			
			dlg2.addArgs(['--targets', tarFile]); # list of files to commit
			dlg2.addArgs(['--force-log', '-F', logFile]); # log message - must have one...
			
			# run dialog and perform operation
			dlg2.go();
			dlg2.exec_();
			
			# cleanup temp files
			os.remove(logFile);
			os.remove(tarFile);
			
			# now schedule update to status list
			self.svnRefreshStatus();
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
class DualityWindow(QMainWindow):
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
		super(DualityWindow, self).__init__(parent);
		
		# main window settings
		self.setWindowTitle('Duality SVN');
		
		# register "actions"
		self.setupActions();
		
		# contents
		self.setupUI();
		self.setupMenus();
		
		self.updateProjectWidgets();
	
	# main widget init
	def setupUI(self):
		# dummy widget for MainWindow container
		dw = QWidget();
		self.setCentralWidget(dw);
		
		# main layout container
		self.layout = QVBoxLayout();
		dw.setLayout(self.layout);
		
		# ..........
		
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
		# 1) "directory"
		gbox = QGridLayout();
		self.layout.addLayout(gbox);
		
		# 1.1) directory label
		gbox.addWidget(QLabel("Working Copy:"), 1,1); # r1 c1
		
		# 1.2) directory field
		self.wDirectory = QLineEdit(project.workingCopyDir);
		self.wDirectory.setToolTip("Directory where working copy is located");
		self.wDirectory.textChanged.connect(self.setWorkingCopyDir);
		
		gbox.addWidget(self.wDirectory, 1,2); # r1 c2
		
		# 1.2) browse-button for directory widget
		self.wDirBrowseBut = QPushButton("Browse...");
		self.wDirBrowseBut.clicked.connect(self.dirBrowseCb);
		
		gbox.addWidget(self.wDirBrowseBut, 1,3); # r1 c3
		
	# register "actions" - i.e. operators 
	def setupActions(self):
		# project settings ----------------------
		self.aNewProject = QAction("&New Project", 
			self, shortcut="Ctrl+N", triggered=self.newProject);
		
		self.aLoadProject = QAction("&Open Project",
			self, shortcut="Ctrl+O", triggered=self.loadProject);
			
		self.aSaveProject = QAction("&Save Project",
			self, shortcut="Ctrl+S", triggered=self.saveProject);
		
		# system ---------------------------------
		self.aExit = QAction("E&xit", 
			self, shortcut="Ctrl+Q", triggered=self.close);
			
		# help
		self.aAbout = QAction("&About",
			self, shortcut="F12", triggered=self.aboutInfo);
	
	# setup menu system
	def setupMenus(self):
		# 1) file menu
		self.mFileMenu = self.menuBar().addMenu("&File");
		self.mFileMenu.addAction(self.aNewProject);
		self.mFileMenu.addAction(self.aLoadProject);
		self.mFileMenu.addAction(self.aSaveProject);
		
		self.mFileMenu.addSeparator();
		
		self.mFileMenu.addAction(self.aExit);
		
		# 3) help menu
		self.mHelpMenu = self.menuBar().addMenu("&Help");
		self.mHelpMenu.addAction(self.aAbout);

	# Callbacks ========================================== 
	
	# Update settings ------------------------------------
	
	# update widgets after altering project settings
	def updateProjectWidgets(self):
		# update titlebar
		if project.autofile:
			self.setWindowTitle("Duality SVN");
		else:
			self.setWindowTitle('%s - Duality SVN' % os.path.split(project.fileN)[1]);
		
		# directory
		self.wDirectory.setText(project.workingCopyDir);
		
		# branches
		self.pBranch1.updateProjectWidgets();
		
	
	# Project Settings -----------------------------------
	
	# prompt for saving unsaved file
	def promptSave(self):
		# get outta here if nothing needs doing
		# FIXME: this is almost always outdated!
		if project.unsaved == False:
			return True;
			
		# prompt for saving
		reply = QMessageBox.question(self, 'Unsaved Changes',
			"Some project settings have been changed\nDo you want to save these changes?", 
			QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
			QMessageBox.Save);
		
		if reply == QMessageBox.Save:
			# save then proceed
			self.saveProject();
			return True;
		elif reply == QMessageBox.Discard:
			# can proceed without saving
			return True;
		else:
			# cannot proceed
			return False;
	
	# create new project
	def newProject(self):
		# if unsaved, prompt about that first
		if self.promptSave() == False:
			# abort if didn't manage to save first
			return;
			
		# create a new project, then flush updates
		project.verifyLoadFile(None, True);
		self.updateProjectWidgets();
	
	# load new project
	def loadProject(self):
		# if unsaved, prompt about that first
		if self.promptSave() == False:
			# abort if didn't manage to save first
			return;
		
		# get new filename
		fileName = QFileDialog.getOpenFileName(self, "Open File",
			".",
			"Duality SVN Projects (*.duality)");
		
		# set new filename, and try to load
		if fileName:
			if project.verifyLoadFile(fileName):
				# update all settings
				self.updateProjectWidgets();
			else:
				QMessageBox.warning(self,
					"Load Duality Project",
					"Could not open project.");
					
	# save project settings as-is
	def saveProject(self):
		# if file is "autofile", prompt user for where to save, so that it can be found again
		# - cancel if user cancels without giving a name...
		if project.autofile:
			fileName = QFileDialog.getSaveFileName(self, 
				"Save File", 
				".", 
				"Duality SVN Projects (*.duality)");
			
			if fileName:
				project.fileN = fileName;
			else:
				print "No filename specified. Cancelling save"
				return;
			
		# just save
		project.save();
	
	# Working Copy ---------------------------------------
	
	# Working copy directory browse callback
	def dirBrowseCb(self):
		# get new directory
		newDir = QFileDialog.getExistingDirectory(self, "Open Directory",
			project.workingCopyDir,
			QFileDialog.ShowDirsOnly
			| QFileDialog.DontResolveSymlinks);
		
		# set this directory
		if newDir:
			project.setWorkingCopyDir(str(newDir));
			self.updateProjectWidgets();
			
	# Set working copy directory callback wrapper
	def setWorkingCopyDir(self, value):
		# flush back to project settings, but only if different
		if project.workingCopyDir != str(value):
			project.setWorkingCopyDir(str(value));
		else:
			print "wc paths same"
		
	# System Info ---------------------------------------
	
	# about box
	def aboutInfo(self):
		QMessageBox.about(self, "About Duality SVN",
			"A SVN Client which makes standard branch management fast and easy!")

# -----------------------------------------

app = QApplication(sys.argv)

if len(sys.argv) > 1:
	project = DualitySettings(sys.argv[1]);
else:
	project = DualitySettings();

mainWin = DualityWindow()
mainWin.show()

sys.exit(app.exec_())

###########################################
