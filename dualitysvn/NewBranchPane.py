# Duality SVN
# Original Author: Joshua Leung
#
# New Branch Pane - Panel for setting up new branches

# import all from "dualitysvn" package
from . import *

import linecache

#########################################
# New Branch Operations Panel

# Setup up new branch (from existing)
class NewBranchPanel(QWidget):
	# Setup ===================================
	
	# ctor
	def __init__(self):
		super(NewBranchPanel, self).__init__();
		
		# setup layout manager
		self.layout = QVBoxLayout();
		self.setLayout(self.layout);
		
		# setup UI widgets
		self.setupUI();
		self.updateProjectWidgets();
		
	# setup main widgets
	def setupUI(self):
		# -) little util defines
		
		# -.1) font
		bfont = QFont();
		bfont.setWeight(QFont.Bold);
		
		# ``````````````````
		
		# 1) create new branch help text
		self.layout.addWidget(QLabel("Create new branch from current 'trunk' in working copy:"));
		
		# .................
		
		# 2) new branch settings
		fbox = QFormLayout();
		self.layout.addLayout(fbox);
		
		# 2a) Name . . . . . . . . . . . .
		# TODO: save this to project?
		self.wName = QLineEdit();
		self.wName.setPlaceholderText("e.g. my-new-branch-name");
		self.wName.setToolTip("Name that new branch should be known as");
		self.wName.textChanged.connect(self.validateCreateBranchOk);
		
		fbox.addRow("Name:", self.wName);
		
		# spacer . . . . . . . . . . . .
		fbox.addItem(QSpacerItem(0,15)); # vertical spacer
		
		# 2b) URL's . . . . . . . . . . . 
		# 2b.1) src trunk
		self.wOldUrl = QLineEdit();
		self.wOldUrl.setToolTip("URL pointing to the 'Trunk' to branch from");
		
		fbox.addRow("<b>From</b> URL:", self.wOldUrl);
		
		# 2b.2) destination 
		self.wNewUrl = QLineEdit();
		self.wNewUrl.setPlaceholderText("e.g. https://svnroot/project/branches/my-branch");
		self.wNewUrl.setToolTip("URL pointing to where the new branch will be stored in the SVN repository");
		self.wNewUrl.textChanged.connect(self.validateCreateBranchOk);
		
		fbox.addRow("<b>New</b> URL:", self.wNewUrl);
		
		# spacer ..................
		self.layout.addSpacing(15);
		
		# .................
		
		# 4) create branch
		# TODO: this needs validation that all fields are filled in!
		self.wCreateBranch = QPushButton("Create New Branch");
		self.wCreateBranch.setToolTip("Create a new branch using the provided information");
		self.wCreateBranch.setFont(bfont);
		self.wCreateBranch.setEnabled(False); # disabled by default, as nothing can be done yet
		self.wCreateBranch.clicked.connect(self.createNewBranch);
		
		self.layout.addWidget(self.wCreateBranch);
		
		# .................
		
		# TODO: attach to existing branch
		# 	- this is quite tricky to implement, so will leave this for now
		#	  but it is something that teams of devs will need if working on
		#	  some shared branch together unless only single dev can do merging
		
		# padding
		self.layout.addStretch();
		
	# Callbacks ====================================
	
	# UI Fluff -------------------------------------
	
	# Update settings here in response to project change
	# i.e. "reset all"
	def updateProjectWidgets(self):
		# clear all/update from project for text fields
		self.wOldUrl.setReadOnly(False); # temp disable for setting
		self.wOldUrl.setText(project.urlTrunk);
		self.wOldUrl.setReadOnly(True);
		
		# init new url from trunk as base, so that less typing is needed
		self.wNewUrl.setText(project.urlTrunk);
		
	# All new-branch fields will trigger this callback when edited, to validate the create branch button
	def validateCreateBranchOk(self):
		# get text field values
		nUrl = str(self.wNewUrl.text());
		name = str(self.wName.text());
		
		# new url must exist, and not be same as previous
		if not nUrl:
			self.wCreateBranch.setEnabled(False);
		elif nUrl == project.urlTrunk:
			self.wCreateBranch.setEnabled(False);
		# name is really only needed for commit-log currently
		elif not name:
			self.wCreateBranch.setEnabled(False);
			
		# should be good to go
		else:
			self.wCreateBranch.setEnabled(True);
		
	# SVN Operations --------------------------------
	
	# create branch
	# TODO: do status updates as this process proceeds...
	def createNewBranch(self):
		# grab vars for easier work
		srcdir = project.workingCopyDir;
		source = str(self.wOldUrl.text());
		target = str(self.wNewUrl.text());
		branchName = str(self.wName.text());
		
		# make a copy of the existing svn metadata - i.e. setup "trunk" copy as "branch2"
		# TODO: make this attach to some process (dp)
		print "Setting up Working Copy Duality..."
		duplicateSvnMetadata(srcdir);
		
		# perform an "svn copy" operation to make a new branch on the repository
		# 	WC + URL = instant commit 
		bp = SvnOperationProcess(self, "Create New Branch (Commit)");
		
		bp.setupEnv(BranchType.TYPE_TRUNK); # can only branch from a "trunk"
		
		bp.setOp("co");
		bp.addArgs([srcdir, target]); # from, to
		bp.addArgs(['-m', "Creating '%s' branch from'%s'\n\nCourtesy of Duality SVN" % (branchName, source)]); # commit log message
		
		
		# change working copy to the branch now
		print "Switching Working Copy to New Branch..."
		sp = SvnOperationProcess(self, "Switch Working Copy to New Branch");
		
		sp.setupEnv(BranchType.TYPE_TRUNK); # we're still in "trunk"
		
		sp.setOp("switch");
		sp.addArgs([target]); # url to switch to
		
		
		# setup dialog to perform operations
		dlg = SvnOperationDialog(self, "Create New Branch");
		
		#dlg.addProcess(dp);
		dlg.addProcess(bp);
		dlg.addProcess(sp);
		
		dlg.go();
		
		# send signal for updating branch tabs, but only if successful
		if dlg.status == ProcessStatus.STATUS_FINISHED:
			self.emit(SIGNAL('projectBranchesChanged()'));

#########################################
# Branch Checkout Panel

# Checkout a branch from SVN
# - to be shown when the user creates a new project from scratch
#   where there isn't any existing SVN content already
class CheckoutBranchPanel(QWidget):
	# Setup ====================================
	
	# ctor
	def __init__(self):
		super(CheckoutBranchPanel, self).__init__();
		
		# setup layout manager
		self.layout = QVBoxLayout();
		self.setLayout(self.layout);
		
		# setup UI widgets
		self.setupUI();
		
	# setup main widgets
	def setupUI(self):
		# -) little util defines
		
		# -.1) font
		bfont = QFont();
		bfont.setWeight(QFont.Bold);
		
		# ``````````````````
		
		# 1) help text
		helpTxt = """\
To begin working with SVN, you need to firstly set up a 
"working copy" of the repository by "checking out" a
copy of the current state of the repository.
		"""
		self.layout.addWidget(QLabel(helpTxt));
		
		# ..................
		
		# 2) URL widget
		gbox = QGridLayout();
		self.layout.addLayout(gbox);
		
		# 2.1) url label
		gbox.addWidget(QLabel("URL:"), 1,1); # r1 c1
		
		# 2.2) directory field
		self.wUrl = QLineEdit();
		self.wUrl.setPlaceholderText("e.g. https://svnroot/project/my-branch");
		self.wUrl.setToolTip("URL pointing to where the branch is stored in the SVN repository");
		self.wUrl.textChanged.connect(self.validateUrl);
		
		gbox.addWidget(self.wUrl, 1,2); # r1 c2
		
		# spacer ..................
		self.layout.addSpacing(15);
		
		# ..................
		
		# 3) authenticiation crap
		# TODO: have this whole box toggle-able for enabled status?
		gb = QGroupBox("Login Details (if necessary)");
		self.layout.addWidget(gb);
		
		grp = QFormLayout();
		gb.setLayout(grp);
		
		# 3.1) username
		self.wUsrName = QLineEdit();
		self.wUsrName.setPlaceholderText("SVN Account Username");
		self.wUsrName.setToolTip("Username for account to access SVN repository with");
		
		grp.addRow(QLabel("Name:"), self.wUsrName);
		
		# 3.2) password
		self.wUsrPass = QLineEdit();
		self.wUsrPass.setPlaceholderText("SVN Account Password");
		self.wUsrPass.setToolTip("Password for account to access SVN respository with. (This is NOT saved to project settings file)");
		self.wUsrPass.setEchoMode(QLineEdit.PasswordEchoOnEdit);
		
		grp.addRow(QLabel("Password:"), self.wUsrPass);
		
		# spacer ..................
		self.layout.addSpacing(30);
		
		# .........................
		
		# 4) Checkout
		self.wCheckout = QPushButton("SVN Checkout");
		self.wCheckout.setToolTip("Download a copy of the current state of the working copy");
		self.wCheckout.setFont(bfont);
		self.wCheckout.clicked.connect(self.svnCheckout);
		
		self.layout.addWidget(self.wCheckout);
		
		# spacer ..................
		self.layout.addSpacing(40);
		
		
		# `````````````````````````````````````````````
		
		# 5) "advanced options"
		self.layout.addWidget(QLabel("Alternative Setup Options:"));
		
		# 5a) setup from existing checkout
		self.wFromExisting = QPushButton("From Existing Checkout...");
		self.wFromExisting.setToolTip("Attach Duality to existing SVN working copy checkout");
		self.wFromExisting.setFont(bfont);
		self.wFromExisting.clicked.connect(self.fromExisting);
		
		self.layout.addWidget(self.wFromExisting);
		
		# spacer ..................
		self.layout.addSpacing(50); # pad out rest of space
		
		
	# Callbacks ====================================
	
	# UI Fluff -------------------------------------
	
	# Update settings here in response to project change
	# i.e. "reset all"
	def updateProjectWidgets(self):
		# clear all text fields
		self.wUrl.setText("");
		
		self.wUsrName.setText("");
		self.wUsrPass.setText("");
	
	# Verify whether checkout can proceed
	def validateUrl(self):
		# get URL
		# TODO: try pinging this URL to test validity
		url = str(self.wUrl.text());
		
		# only if there is content, may we continue...
		self.wCheckout.setEnabled(len(url));
		
	# SVN Ops --------------------------------------
	
	# do the actual checkout
	def svnCheckout(self):
		QMessageBox.warning(self, 
			"Checkout",
			"Feature not yet implemented!");
		
		# prepare SVN process
		
		# if successful, set project's new working copy + url settings
		
	# ...........................
	
	# setup from existing checkout
	def fromExisting(self):
		# verify that the "working directory" specified exists
		if os.path.exists(project.workingCopyDir) == False:
			QMessageBox.warning(self, 
				"Setup from existing...", 
				"Working Copy Directory does not exist");
			return;
			
		# try to find an svn directory in there
		if os.path.exists(os.path.join(project.workingCopyDir, ".svn")) == False:
			QMessageBox.warning(self, 
				"Setup from existing...", 
				"This does not appear to be a valid SVN working copy.\n\nNo SVN Metadata was found in:\n"+project.workingCopyDir);
			return;
		
		# grab URL
		# - we could do this by running "svn info" and parsing that output, 
		#   but it's easier to just parse the svn metadata directly...
		metaInfoPath = os.path.join(project.workingCopyDir, ".svn", "entries");
		
		if os.path.exists(metaInfoPath):
			# as of svn 1.6.3, the url is line 5 of this file
			project.urlTrunk = linecache.getline(metaInfoPath, 5).rstrip();
		else:
			QMessageBox.critical(self,
				"Setup from existing...",
				"Couldn't find metadata we were looking for");
			return;
			
		# send signal for updating branch tabs
		self.emit(SIGNAL('projectBranchesChanged()'));

#########################################
