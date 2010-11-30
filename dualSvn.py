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
	
# Get list of changed files
def svnGetChangedFiles(srcdir):
	pass;
	
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
# Data Model

import ConfigParser

# Defines all the critical configuration information for
# branching management
class ConfigProfile:
	# Instance Variables ============================
	__slots__ = (
		'srcdir',		# (str) directory where working copy is located
		
		'trunk_url',	# (str) URL for "trunk" SVN Tree
		'branch_url',	# (str) URL for "branch" SVN Tree (when available/in use)
		
		'branch_name' 	# (str) name of the new branch
	);
	
	# ctor
	def __init__(self):
		# init vars
		self.srcdir = ".";
		self.trunk_url = "https://svnroot/trunk";
		self.branch_url = None;
		self.branch_name = None;
		
		# read in profile from "current directory"
		self.loadProfile();
		
	# Load/Save =====================================
	
	# try to open a file-pointer to the file
	def getFp(self, create=False):
		# get filename
		fn = os.path.join(".", "svn_config.duality");
		
		# if 'create', open it for writing
		if create:
			return open(fn, 'w');
		# otherwise, only open for reading if existing
		elif os.path.exists(fn):
			return open(fn, 'r');
		else:
			return None;
	
	# load profile file from current directory
	def load(self):
		f = self.getFp();
		if f:
			# FIXME: use config parser to do this...
			pass
				
				
		
	# save profile to file in current directory
	def save(self):
		f = self.getFp(True);
		
		# write settings
		# FIXME: use config parser to do this
		
		f.close();

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
		
		# create widgets and bind events
			# label
		self.wLabel = QLabel(name + ":");
			# text box
		self.wText = QLineEdit(txt);
		
		# init layout
		hbox = QHBoxLayout();
		self.setLayout(hbox);
		
		# add components to layout
		hbox.addWidget(self.wLabel);
		hbox.addWidget(self.wText);

	# Updates =========================================
	

# -----------------------------------------
# Branch Panes

# Base define for a pane describing a branch
class BranchPane(QGroupBox):
	__slots__ = (
		'layout',		# (QLayout) layout manager for widget
		
		'wUrl',			# (LabelledTextWidget) url of branch in repository
		'wUpdate',		# (QPushButton) svn update
	);
	
	# ctor
	# < title: (str) the label of the box
	def __init__(self, title):
		QGroupBox.__init__(self, title);
		
		# setup layout manager
		self.layout = QVBoxLayout();
		self.setLayout(self.layout);
		
		# init widgets
		self.setupUI();
		
	# main widget init
	def setupUI(self):
		# url widget
		self.wUrl = LabelledTextWidget("URL", "branchUrl", 
			"URL pointing to where the branch is stored in the SVN repository");
		self.layout.addWidget(self.wUrl);
		
		# space
		self.layout.addSpacing(15);
		
		# update from repository
		self.wUpdate = QPushButton("SVN Update");
		self.layout.addWidget(self.wUpdate);
		
		# space
		self.layout.addSpacing(15);
		
		# status
		self.layout.addWidget(QLabel("Status:"))
		

# -----------------------------------------
# Working Copy Pane

class WorkingCopyPane(QGroupBox):
	def __init__(self):
		QGroupBox.__init__(self, "Working Copy");
		
		hbox = QHBoxLayout();
		self.setLayout(hbox);
		
		# left
		vbox = QVBoxLayout();
		hbox.addLayout(vbox);
		
		self.wAdd = QPushButton("Add Files/Directories");
		vbox.addWidget(self.wAdd);
		
		self.wRename = QPushButton("Rename Files/Directories");
		vbox.addWidget(self.wRename);
		
		self.wDelete = QPushButton("Delete Files/Directories");
		vbox.addWidget(self.wDelete);
		
		# right
		vbox = QVBoxLayout();
		hbox.addLayout(vbox);
		
		self.wApplyPatch = QPushButton("Apply Patch");
		vbox.addWidget(self.wApplyPatch);
		
		self.wExport = QPushButton("Export");
		vbox.addWidget(self.wExport);

# -----------------------------------------
# Main Window

# Main Window
class DualityWindow(QWidget):
	# Class Defines ==================================
	
	# Instance Vars ==================================
	
	__slots__ = (
		'wDirectory',
		'pBranch1',
		'pBranch2',
		'pWorkingCopy'
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
		mainVBox.addWidget(self.wDirectory)
		
		# 2) layout container for the branch-option containers
		hbox = QHBoxLayout();
		mainVBox.addLayout(hbox);
		
		# 2a) left branch - main
		self.pBranch1 = BranchPane("Branch");
		hbox.addWidget(self.pBranch1);
		
		# 2b) right branch - secondary
		self.pBranch2 = BranchPane("Trunk");
		hbox.addWidget(self.pBranch2);
		
		# 3) working copy panel
		self.pWorkingCopy = WorkingCopyPane();
		mainVBox.addWidget(self.pWorkingCopy);

# -----------------------------------------
	
app = QApplication(sys.argv)

mainWin = DualityWindow()
mainWin.show()

sys.exit(app.exec_())

###########################################
