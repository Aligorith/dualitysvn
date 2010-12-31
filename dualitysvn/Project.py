# Duality SVN
# Original Author: Joshua Leung
#
# Project Settings

import os
import ConfigParser

##########################
# Settings Container ("project")

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
		#'nameTrunk',			# (str) user-assigned name for "trunk"
		
		'urlBranch',		# (str) url of "branch"
		'nameBranch', 		# (str) user-assigned name for "branch"
		
		'activeTabIndex',	# (int) active tab index
		
		'skiplist',			# (list<str>) list of paths to ignore in our UI only - i.e. with temp changes we don't want shared yet
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
			# make sure it is a string before verifying
			fileN = str(fileN);
			
			if os.path.exists(fileN):
				# save filename and try to load stored settings
				self.fileN = fileN;
				self.load();
			else:
				# nullify and fall back on next step...
				fileN = None;
		
		# create default filename otherwise...
		if (fileN is None) and (addIfInvalid):
			# clear all old project settings first
			self.resetDefaults();
			
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
		self.workingCopyDir = os.getcwd();		
		
		# trunk should be clear at startup - users can then set their own trunk
		self.urlTrunk = None;
		
		# no branches by default!
		self.urlBranch = None; 
		self.nameBranch = None;
		
		# active tab index
		self.activeTabIndex = 0;
		
		# list of files to ignore in status list (to protect local-only changes from accidental changes)
		self.skiplist = set();
		
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
			self.activeTabIndex = cfg.getint("Project", "ActiveTabIndex");
			
			self.urlTrunk = cfg.get("Trunk", "url");
			
			if cfg.has_section("Branch"):
				self.urlBranch = cfg.get("Branch", "url");
				self.nameBranch = cfg.get("Branch", "name");
				
			# load skiplist section
			# 	- currently, this is just a section with a list of items without any values 
			for name,val in cfg.items("Skip-List"):
				self.skiplist.add(name);
			
			
	# Save config file
	def save(self):
		# create parser
		cfg = ConfigParser.SafeConfigParser();
		
		# load in the settings
		cfg.add_section("Project");
		cfg.set("Project", "WorkingCopy", self.workingCopyDir);
		cfg.set("Project", "ActiveTabIndex", str(self.activeTabIndex));
		
		cfg.add_section("Trunk");
		cfg.set("Trunk", "url", self.urlTrunk);
		
		if self.urlBranch:
			cfg.add_section("Branch");
			cfg.set("Branch", "url", self.urlBranch);
			cfg.set("Branch", "name", self.nameBranch);
			
		# skiplist section
		cfg.add_section("Skip-List");
		for path in self.skiplist:
			cfg.set("Skip-List", path, "");
			
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
		
	# < value: (int) new value
	def setActiveTabIndex(self, value):
		self.activeTabIndex = value;
		# no need to set "unsaved" as this is more of a UI state only
	
	# < value: (str) new value
	def setUrlTrunk(self, value):
		self.urlTrunk = value;
		self.unsaved = True;
		
	# < value: (str) new value
	def setUrlBranch(self, value):
		self.urlBranch = value;
		self.unsaved = True;
		
	# ------------------------------
		
	# < value: (str) path to add to list of paths to ignore
	# TODO: in future, store these with associated but still optional "reasons"
	def addSkipPath(self, value):
		self.skiplist.add(value);
		self.unsaved = True;
		
	# clear out all entries from skip list
	def clearSkipList(self):
		# clear if non-empty
		if len(self.skiplist):
			self.skiplist.clear();
			self.unsaved = True;

##########################
