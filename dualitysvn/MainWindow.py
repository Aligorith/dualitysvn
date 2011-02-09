# Duality SVN
# Original Author: Joshua Leung
#
# Main Window

from coreDefines import *

from BranchPane import *
from NewBranchPane import *

#########################################

# Main Window
class DualityWindow(QMainWindow):
	# Class Defines ==================================
	
	# Instance Vars ==================================
	
	__slots__ = (
		'layout',
		
		'wDirectory',
		'wDirBrowseBut',
		
		'wTabs',
	);
	
	# Setup ========================================== 
	
	# ctor
	def __init__(self, parent=None):
		# toplevel 'widget' (i.e. window) - no parent
		super(DualityWindow, self).__init__(parent);
		
		# main window settings
		self.setWindowTitle('Duality SVN');
		self.setWindowIcon(QIcon('icons/duality_logo.png'))
		
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
		# TODO: should the various tabs only be created if/when they're needed instead?
		self.wTabs = QTabWidget();
		self.wTabs.currentChanged.connect(project.setActiveTabIndex);
		
		self.layout.addWidget(self.wTabs);
		
		# prepare the tab panels first
		self.pCheckout = None; # checkout repository for new project
		self.pBranching = None; # create branch of trunk
		
		self.pTrunk = None; # trunk panel
		self.pBranch = None; # branch panel
		
	# setup working copy panel
	def setupWorkingCopyPanel(self):
		# 1) "directory"
		gbox = QGridLayout();
		self.layout.addLayout(gbox);
		
		# 1.1) directory label
		gbox.addWidget(QLabel("Working Copy:"), 1,1); # r1 c1
		
		# 1.2) directory field
		# TODO: setup red-highlight when directory doesn't exist!
		if project.workingCopyDir:
			self.wDirectory = QLineEdit(project.workingCopyDir);
		else:
			self.wDirectory = QLineEdit();
		self.wDirectory.setToolTip("Directory where working copy is located");
		self.wDirectory.setPlaceholderText("e.g. ./src/");
		self.wDirectory.setFocusPolicy(Qt.ClickFocus); # it shouldn't gain focus by itself or through tabbing!
		
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
		
		
		self.aProjectConfig = QAction("Project Configuration",
			self, triggered=self.projectConfig);
		
		self.aSvnConfig = QAction("SVN Configuration",
			self, triggered=self.svnConfig);
		
		# system ---------------------------------
		self.aExit = QAction("E&xit", 
			self, shortcut="Ctrl+Q", triggered=self.close);
			
		# edit -----------------------------------
		self.aCleanup = QAction("&Cleanup (Fix SVN Errors)",
			self, triggered=self.branchCleanup);
			
		# help -----------------------------------
		self.aAbout = QAction("&About",
			self, shortcut="F12", triggered=self.aboutInfo);
		self.aAboutQt = QAction("About Qt",
			self, triggered=QApplication.aboutQt);
	
	# setup menu system
	def setupMenus(self):
		# 1) file menu
		self.mFileMenu = self.menuBar().addMenu("&File");
		self.mFileMenu.addAction(self.aNewProject);
		self.mFileMenu.addAction(self.aLoadProject);
		self.mFileMenu.addAction(self.aSaveProject);
		
		self.mFileMenu.addSeparator();
		
		self.mFileMenu.addAction(self.aProjectConfig);
		self.mFileMenu.addAction(self.aSvnConfig);
		
		self.mFileMenu.addSeparator();
		
		self.mFileMenu.addAction(self.aExit);
		
		# 2) branch menu
		self.mEditMenu = self.menuBar().addMenu("&Edit");
		#self.mEditMenu.addAction("Show Log"); # FIXME: placeholder
		self.mEditMenu.addAction(self.aCleanup);
		self.mEditMenu.addAction("Edit Conflicts"); # FIXME: placeholder
		
		# 3) help menu
		self.mHelpMenu = self.menuBar().addMenu("&Help");
		self.mHelpMenu.addAction(self.aAbout);
		self.mHelpMenu.addAction(self.aAboutQt);

	# Helper Methods ===================================== 
	
	# Get the panel for the active branch (if available)
	# > return[0]: (BranchPane) branch panel for active tab if applicable
	def getActiveBranchTab(self):
		# gets the panel associated with the active tab directly
		actPane = self.wTabs.currentWidget();
		
		# check if branch
		if isinstance(actPane, BranchPanel):
			return actPane;
		else:
			return None;
	
	# Callbacks ========================================== 
	
	# Update settings ------------------------------------
	
	# update widgets after altering project settings
	# - optional args are used to specify if only "smaller" cases occurred
	# FIXME: this method needs a good rethink/recode???
	def updateProjectWidgets(self, workingCopyChanged=False):
		# update titlebar
		if project.autofile:
			self.setWindowTitle("Duality SVN");
		elif project.unsaved:
			self.setWindowtitle('%s* - Duality SVN' % os.path.split(project.fileN)[1]);
		else:
			self.setWindowTitle('%s - Duality SVN' % os.path.split(project.fileN)[1]);
		
		# directory
		if workingCopyChanged == False:
			self.wDirectory.setText(project.workingCopyDir);
		
		# branches
		self.updateVisibleBranches();
		
	# determine visible branches, updating as necessary
	# TODO: need a way to signal destructive update - i.e. project changed!
	def updateVisibleBranches(self):
		# clear all tabs first 
		#	- need to save active tab index before doing so, as clearing tabs will reset this
		activeTabIndex = project.activeTabIndex;
		
		self.wTabs.clear();
		
		# checkout ..........................
		
		# if trunk isn't set, then we only need the setup pane
		if not project.urlTrunk:
			# create panel if necessary
			if self.pCheckout is None:
				self.pCheckout = CheckoutBranchPanel();
				
			# hook up tab
			self.wTabs.addTab(self.pCheckout, "Setup Project");
			self.wTabs.setTabToolTip(0, "Set up working copy sandbox for project");
			
			# hook up setup done event
			self.connect(self.pCheckout, SIGNAL('projectBranchesChanged()'), self.updateVisibleBranches);
			
			return;
		
		# trunk .............................
		
		# trunk type - reference or standard?
		if project.urlBranch:
			trunkType = BranchType.TYPE_TRUNK_REF;
			trunkLabel = "[Trunk]";
			toolTip = "<i>Secondary branch</i> - 'Trunk' from which development branch was branched from";
		else:
			trunkType = BranchType.TYPE_TRUNK;
			trunkLabel = "Trunk";
			toolTip = "<i>Primary branch</i> - Development in working copy directly corresponds to this branch (usually Trunk branch) in the repository";
		
		# create new or make sure type is up to date
		if self.pTrunk is None:
			self.pTrunk = BranchPanel(trunkType);
		else:
			# change type and update as necessary
			self.pTrunk.changeBranchType(trunkType);
		self.pTrunk.updateProjectWidgets();
			
		# hook up tab
		self.wTabs.addTab(self.pTrunk, trunkLabel);
		self.wTabs.setTabToolTip(1, toolTip);
		
		# branch .............................
		
		# create branch or show branch details?
		if project.urlBranch:
			# branch exists, so show branch work pane
			if self.pBranch is None:
				self.pBranch = BranchPanel(BranchType.TYPE_BRANCH);
			self.wTabs.addTab(self.pBranch, "Branch");
			self.wTabs.setTabToolTip(2, "<i>Primary branch</i> - Development in working copy directly corresponds to this branch, which was branched from the Secondary (Trunk)");
		else:
			# branch doesn't exist, so show create branch pane
			if self.pBranching is None:
				self.pBranching = NewBranchPanel();
			self.wTabs.addTab(self.pBranching, "+");
			self.wTabs.setTabToolTip(2, "Create new branch from Primary branch");
			
		# `````````````````````````
		
		# set active tab (from pre-saved value)
		self.wTabs.setCurrentIndex(activeTabIndex);
	
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
			print "prompt save failed - new project"
			return;
			
		# create a new project, then flush updates
		project.verifyLoadFile(None, True);
		self.updateProjectWidgets();
	
	# load new project
	def loadProject(self):
		# if unsaved, prompt about that first
		if self.promptSave() == False:
			# abort if didn't manage to save first
			print "prompt save failed - load project"
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
		# check whether we can save yet
		if not project.workingCopyDir:
			QMessageBox.warning(self, 	
				"Save Duality Project",
				"Cannot save with Working Copy Directory undefined");
			return;
		elif not project.urlTrunk:
			QMessageBox.warning(self,
				"Save Duality Project",
				"Cannot save with no 'Trunk' URL defined");
			return;
		
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
		print "Saved"
		
	# override window close to prompt for saving
	def closeEvent(self, event):
		if self.promptSave():
			# accept close event, and exit
			# 	- file will already have been saved, as handled by promptSave()
			event.accept();
		else:
			# don't quit yet
			event.ignore();
	
	# Settings -------------------------------------------
	
	def projectConfig(self):
		print "Project Settings Config dialog"
		# - temp-dir for log/target files
	
	
	def svnConfig(self):
		print "SVN Settings Config dialog"
	
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
			self.updateProjectWidgets(workingCopyChanged=True);
			
	# Set working copy directory callback wrapper
	def setWorkingCopyDir(self, value):
		# flush back to project settings, but only if different
		if project.workingCopyDir != str(value):
			project.setWorkingCopyDir(str(value));
			self.updateProjectWidgets(workingCopyChanged=True);
		else:
			print "wc paths same"
		
	# Branch Tools --------------------------------------
	
	# Cleanup svn metadata
	def branchCleanup(self):
		# call the cleanup op on the branch (if available)
		branch = self.getActiveBranchTab();
		
		if branch:
			branch.svnCleanup();
	
	# System Info ---------------------------------------
	
	# about box
	def aboutInfo(self):
		aboutText  = "<p><b>Duality SVN</b><br>"
		aboutText += "Version: %s<br>" % (DUALITY_VERSION_STRING)
		aboutText += "By Joshua Leung</p>"
		aboutText += "<p>A SVN Client which makes working version control with SVN "
		aboutText += "easy, with simple branch management for real people.</p>"
		
		QMessageBox.about(self, "About Duality SVN", aboutText);

#########################################
