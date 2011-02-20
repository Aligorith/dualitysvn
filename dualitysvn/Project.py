# Duality SVN
# Original Author: Joshua Leung
#
# Project Settings

import os
import tempfile

import ConfigParser

import traceback

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
		'tempFileDir',		# (str) directory where temporary files should get saved
		
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
		
		# "temp" dir should just be system default?
		self.tempFileDir = tempfile.gettempdir();
		
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
		
		# if filename is a directory, user is trying to use "new from existing checkout"
		# so we should load up the relevant info from that instead
		if os.path.isdir(self.fileN):
			# "filename" is really a directory, so store that as our working copy directory
			self.workingCopyDir = self.fileN;
			
			# clear fileN by revalidating it (so that user has option of saving a proper config later
			self.fileN = verifyLoadFile(None);
			
			# check for .svn folder, and try to find out URL...
			# XXX: for now, just let user have to manually set up "new existing checkout" to complete the process
		else:
			# grab filepointer and read file
			with open(self.fileN, 'r') as f:
				# create parser
				cfg = TameConfigParser();
				
				# read file to populate parser's buffer
				cfg.readfp(f);
				
				# grab the values for the various parts
				cfg.get("Project", "WorkingCopy", self, 'workingCopyDir');
				cfg.get("Project", "TempFiles", self, 'tempFilesDir');
				
				cfg.getint("Project", "ActiveTabIndex", self, 'activeTabIndex');
				
				cfg.get("Trunk", "url", self, 'urlTrunk');
				
				if cfg.has_section("Branch"):
					cfg.get("Branch", "url", self, 'urlBranch');
					cfg.get("Branch", "name", self, 'nameBranch');
					
				# load skiplist section
				# 	- currently, this is just a section with a list of items without any values 
				for name,val in cfg.items("Skip-List"):
					self.skiplist.add(name);
			
			
	# Save config file
	def save(self):
		# create parser
		cfg = TameConfigParser()
		
		# load in the settings
		cfg.add_section("Project");
		cfg.set("Project", "WorkingCopy", self.workingCopyDir);
		cfg.set("Project", "TempFiles", self.tempFileDir);
		
		cfg.set("Project", "ActiveTabIndex", self.activeTabIndex);
		
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
	
	# Get the type of the active branch tab
	# ! Keep this in sync with the logic in MainWindow.updateVisibleBranches()
	# > returns BranchType.TYPE_* or None
	def getActiveBranchType(self):
		# if active tab is 2, it must be the branch
		if self.activeTabIndex == 2:
			return BranchType.TYPE_BRANCH;
			
		# if active tab is 1, then it is either trunk or trunk-reference
		elif self.activeTabIndex == 1:
			if self.urlBranch:
				return BranchType.TYPE_TRUNK_REF;
			else:
				return BranchType.TYPE_TRUNK;
		
		# otherwise, there isn't a branch!
		else:
			return None;
	
	# Setters =================================
	# Note: these setters MUST be used, otherwise, we don't get the the unsaved tag being set (causing problems later)
	
	# < value: (str) new value
	def setWorkingCopyDir(self, value):
		self.workingCopyDir = str(value);
		self.unsaved = True;
		
	# < value: (str) new value
	def setTempFileDir(self, value):	
		self.tempFileDir = str(value);
		self.unsaved = True;
		
	# < value: (int) new value
	def setActiveTabIndex(self, value):
		self.activeTabIndex = int(value);
		# no need to set "unsaved" as this is more of a UI state only
	
	# < value: (str) new value
	def setUrlTrunk(self, value):
		self.urlTrunk = str(value);
		self.unsaved = True;
		
	# < value: (str) new value
	def setUrlBranch(self, value):
		self.urlBranch = str(value);
		self.unsaved = True;
		
	# ------------------------------
		
	# < value: (str) path to add to list of paths to ignore
	# TODO: in future, store these with associated but still optional "reasons"
	def addSkipPath(self, value):
		self.skiplist.add(str(value));
		self.unsaved = True;
		
	# < value: (str) path to remove from list of paths to ignore
	def removeSkipPath(self, value):
		self.skiplist.remove(str(value));
		self.unsaved = True;
		
	# clear out all entries from skip list
	def clearSkipList(self):
		# clear if non-empty
		if len(self.skiplist):
			self.skiplist.clear();
			self.unsaved = True;

##########################
# Config Parser that doesn't throw up on errors

class TameConfigParser(ConfigParser.SafeConfigParser):
	# Setup ==========================================================
	
	def __init__(self):
		# init internal reference 
		#super(TameConfigParser, self).__init__(); # XXX: why doesn't this work!
		ConfigParser.SafeConfigParser.__init__(self);
		
		# set all the settings we need to make it tame
		self.optionxform = str # don't munge case!
	
	# Exceptions Supressed Wrapper Methods ============================
	
	# Getters ---------------------------------------------------------
	
	# we can only 'get' the value of an existing item 
	# < getCb: (fn(cfg, section, option)) callback used for actually getting the value
	# < (targetObj/targetVar): when defined (BOTH need to be together), then the value is read directly
	#		into the variable named by "targetVar" in "targetObj"
	def _get_helper(self, section, option, getCb, targetObj=None, targetVar=None):
		# try to get value from backend
		if self.has_option(section, option):
			val = getCb(self, section, option);
		else:
			val = None;
		
		# if both settings for where to set the value are given, perform the setting
		if targetObj and targetVar:
			# try to set by hacking through the dict, which should always be available
			targetObj.__dict__[targetVar] = val;
		else:
			return val;
	
	# .........
	
	# safety wrapper around standard get()
	def get(self, section, option, targetObj=None, targetVar=None):
		return self._get_helper(section, option, 
				#super(type(self), self).get,  # XXX: why doesn't this work!
				ConfigParser.SafeConfigParser.get, 
				targetObj, targetVar);
				
	# safety wrapper around standard getint()
	def getint(self, section, option, targetObj=None, targetVar=None):
		return self._get_helper(section, option,
				#super(type(self), self).getint, # XXX: why doesn't this work!
				ConfigParser.SafeConfigParser.getint,
				targetObj, targetVar);
				
	# safety wrapper around standard getfloat()
	def getfloat(self, section, option, targetObj=None, targetVar=None):
		return self._get_helper(section, option,
				#super(type(self), self).getfloat, # XXX: why doesn't this work!
				ConfigParser.SafeConfigParser.getfloat,
				targetObj, targetVar);
				
	# safety wrapper around standard getboolean()
	def getboolean(self, section, option, targetObj=None, targetVar=None):
		return self._get_helper(section, option,
				#super(type(self), self).getboolean, # XXX: why doesn't this work!
				ConfigParser.SafeConfigParser.getboolean,
				targetObj, targetVar);
		
	# Setters -----------------------------------------------------------
	
	# safety wrapper around "set()" method, which ensures that only strings get written
	# and the section has been validated
	def set(self, section, option, value):
		if self.has_section(section):
			#super(type(self), self).set(section, option, str(value)); # XXX: why doesn't this work!
			ConfigParser.SafeConfigParser.set(self, section, option, str(value));
		else:
			print "Config I/O ERROR: Trying to set value in non-existing section... (%s)" % (section)
			traceback.print_stack();
	

##########################
