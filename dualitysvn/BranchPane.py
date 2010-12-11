# Duality SVN
# Original Author: Joshua Leung
#
# Branch Pane - Panel representing the main UI for a branch

# import all from "dualitysvn" package
from . import *

#########################################

# Base define for a pane describing a branch
class BranchPane(QWidget):
	# Instance Settings ====================================================
	__slots__ = (
		# Model .......................................................
		'branchType',		# (int) type of the branch (BranchType.TYPE_*)
		
		# General Layout Stuff ........................................
		'layout',			# (QLayout) layout manager for widget
		
		# Widgets Stuff ...............................................
		'wUrl',				# (LabelledTextWidget) url of branch in repository
		'wUpdate',			# (QPushButton) svn update
		'wApplyPatch',  	# (QPushButton) apply patch
		
		'wRefreshStatus',  	# (QPushButton) refresh status of 'status' box
		'wStatusView',		# (SvnStatusList) list view
		
		'wAdd',				# (QPushButton) svn add
		'wDelete',			# (QPushButton) svn delete
		
		'wRevert',			# (QPushButton) svn revert
		
		'wCreatePatch',		# (QPushButton) create patch (i.e. svn diff)
		
		'wCommit',			# (QPushButton) svn commit - to main branch
		
		# Refresh Stuff ................................................
		'refreshProcess',	# (QProcess) process used to refresh the status list - only defined while in use
	);
	
	# Setup ================================================================
	
	# ctor
	def __init__(self, branchType):
		super(BranchPane, self).__init__();
		
		# setup internal settings
		self.branchType = branchType;
		
		self.refreshProcess = None;
		
		# setup layout manager
		self.layout = QVBoxLayout();
		self.setLayout(self.layout);
		
		# init widgets
		self.setupUI();
		self.updateActionWidgets();
		
	# main widget init
	def setupUI(self):
		# -) little util defines
		
		# -.1) font
		bfont = QFont();
		bfont.setWeight(QFont.Bold);
		
		# ``````````````````
		
		# 1) url widget
		gbox = QGridLayout();
		self.layout.addLayout(gbox);
		
		# 1.1) url label
		gbox.addWidget(QLabel("URL:"), 1,1); # r1 c1
		
		# 1.2) directory field
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
		self.wUpdate.setToolTip("Fetch and apply recent changes made to the repository to working copy");
		self.wUpdate.setFont(bfont);
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
		self.wRefreshStatus.setToolTip("Refresh the list of paths shown and their current versioning status");
		self.wRefreshStatus.setFont(bfont);
		self.wRefreshStatus.clicked.connect(self.svnRefreshStatus);
		
		self.wRefreshStatus.setVisible(True);
		gbox.addWidget(self.wRefreshStatus, 1,4); # r1 c4
		
		# 3.1c2) "stop refresh" button - only visible when needed
		self.wStopRefreshStatus = QPushButton("Stop");
		self.wStopRefreshStatus.setToolTip("Stop refreshing the status list");
		self.wStopRefreshStatus.clicked.connect(self.stopRefreshStatus);
		
		self.wStopRefreshStatus.setVisible(False);
		gbox.addWidget(self.wStopRefreshStatus, 1,4); # r1 c4
		
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
		if self.branchType == BranchType.TYPE_TRUNK_REF:
			self.wCommit = QPushButton("Reintegrate Branch Changes");
			self.wCommit.setToolTip("Apply all changes made in branch back to trunk (from which it was originally branched from)");
			self.wCommit.clicked.connect(self.svnReintegrate);
		else:
			self.wCommit = QPushButton("Commit");
			self.wCommit.setToolTip("Send selected changes in working copy to repository");
			self.wCommit.setFont(bfont);
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
		if self.branchType == BranchType.TYPE_BRANCH:
			self.wUrl.setText(project.urlBranch);
			self.wUrl.setReadOnly(True);
		elif self.branchType == BranchType.TYPE_TRUNK_REF:
			self.wUrl.setText(project.urlTrunk);
			self.wUrl.setReadOnly(True);
		else:
			self.wUrl.setText(project.urlTrunk);
			self.wUrl.setReadOnly(False);
		
		# clear status list
		self.wStatusView.model.clearAll();
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
	
	# toggle selected items
	def statusToggleAll(self):
		# call toggle on list model
		# TODO: should status view provide a wrapper for this?
		self.wStatusView.model.toggleAllChecked();
		
		# update widgets
		self.updateActionWidgets();
	
	# Status List Refresh ---------------------------------------------------------
	
	# refresh status list
	def svnRefreshStatus(self):
		# this is just an alias for the start of the refresh process
		self.startRefreshStatus();
	
	# ..................
	
	# refresh launcher
	def startRefreshStatus(self):
		# clear list's model
		self.wStatusView.model.clearAll();
		
		# tweak the buttons shown
		self.wRefreshStatus.setVisible(False);
		self.wStopRefreshStatus.setVisible(True);
		
		self.updateActionWidgets(); # do this too, as we could be here quite a while...
		
		# setup up process that performs the reading
		self.refreshProcess = QProcess();
		
		self.connect(self.refreshProcess, SIGNAL("readyReadStandardOutput()"), self.readRefreshStatusInfo);
		self.connect(self.refreshProcess, SIGNAL("finished(int, QProcess::ExitStatus)"), self.endedRefreshStatus);
		
		# setup stuff from SvnOperationDialog.setupEnv()
		# TODO: incorporate all this into an abstraction...
		self.refreshProcess.setWorkingDirectory(project.workingCopyDir);
		
		env = QProcessEnvironment.systemEnvironment();
		self.refreshProcess.setProcessEnvironment(env); # assume that we can set this first
		
		useSecondaryBranch = (self.branchType == BranchType.TYPE_TRUNK_REF); 
		if useSecondaryBranch:
			env.insert(SVN_HACK_ENVVAR, "1");
		
		# start the process
		args = ["status"]; # the command
		args += ["--non-interactive", "--ignore-externals"]; # options for background stuff
		
		self.refreshProcess.start("svn", args);
		
	# cleanup after refresh status is done
	def doneRefreshStatus(self):
		# tweak the buttons shown - restore original state
		self.wRefreshStatus.setVisible(True);
		self.wStopRefreshStatus.setVisible(False);
		
		self.updateActionWidgets();
	
	# stop refresh status list
	def stopRefreshStatus(self):
		# kill process - only way to get rid of console apps on windows
		self.refreshProcess.kill();
		
		# cleanup
		self.doneRefreshStatus();
		
	# read refresh-status process output line
	def readRefreshStatusInfo(self):
		# read in line, and chop off newline
		line = str(self.refreshProcess.readLine()).rstrip("\n");
		
		# parse the output to create a new line, and add to model
		if len(line):
			item = SvnStatusListItem(line);
			self.wStatusView.model.add(item);
		
	# callback called when refresh operation finishes
	def endedRefreshStatus(self, exitCode, exitStatus):
		# grab rest of output
		while self.refreshProcess.canReadLine():
			self.readRefreshStatusInfo();
		
		# if exited with some problem, make sure we warn
		# TODO: set own status codes...?
		if exitStatus == QProcess.CrashExit:
			QMessageBox.warning(self,
				"SVN Error",
				"Refresh Status operation was not completed successfully");
		
		# hack: force sorting to be performed again now
		self.wStatusView.setSortingEnabled(True);
		
		# cleanup
		self.doneRefreshStatus();
	
	# Status List Dependent --------------------------------------------------
	
	# error for nothing selected
	def noDataSelectedCb(self, feature):
		QMessageBox.warning(self,
			feature+" Error",
			"No paths selected for %s operation.\nEnable some of the checkboxes beside paths in the Status list and try again." % (feature))
	
	# ...........
	
	# get list of items to operate on
	# > return: (SvnStatusListDatalist)
	def statusListGetOperatable(self):
		return self.wStatusView.getOperationList();
	
	# ...........
	
	def svnAdd(self):
		# get list of files to change
		files = self.statusListGetOperatable();
		if len(files) == 0:
			self.noDataSelectedCb("Add");
			return;
		
		# filter list of files to only include unversioned
		files = files.getFiltered(lambda x: x.file_status == SvnStatusListItem.FileStatusMap['?']);
		
		# dump names of files to commit to another temp file
		tarFile = files.savePathsFile();
		
		# create operation dialog, and prepare it for work
		# TODO: should we do this for both branches at once?
		dlg = SvnOperationDialog(self, "Add");
		dlg.setupEnv(self.branchType);
		dlg.setOp("add");
		
		dlg.addArgs(['--targets', tarFile]); # list of files to add
		dlg.addArgs(['--auto-props']); # automatically set svn-properties on files based on status
		
		# run dialog and perform operation
		dlg.go();
		dlg.exec_();
		
		# cleanup temp files
		os.remove(tarFile);
		
		# now schedule update to status list
		self.svnRefreshStatus();
		
	def svnDelete(self):
		# get list of files to change
		files = self.statusListGetOperatable();
		if len(files) == 0:
			self.noDataSelectedCb("Delete");
			return;
		
		# filter list of files to only include added, conflicted, modified, replaced, or missing
		def filterPredicate(item):
			for k in ('A', 'C', 'M', 'R', '!'):	
				if self.file_status == SvnStatusListItem.FileStatusMap[k]:
					return True;
			else:
				return False;
		files = files.getFiltered(filterPredicate);
		
		# dump names of files to commit to another temp file
		tarFile = files.savePathsFile();
		
		# create operation dialog, and prepare it for work
		# TODO: should we do this for both branches at once?
		dlg = SvnOperationDialog(self, "Delete");
		dlg.setupEnv(self.branchType);
		dlg.setOp("del");
		
		dlg.addArgs(['--targets', tarFile]); # list of files to delete
		#dlg.addArgs(['--keep-local']); # don't delete working copy's copy (TODO: enable this when branched so that we can do the other branch next)
		
		# run dialog and perform operation
		dlg.go();
		dlg.exec_();
		
		# cleanup temp files
		os.remove(tarFile);
		
		# now schedule update to status list
		self.svnRefreshStatus();
		
	def svnRevert(self):
		# get list of files to change
		files = self.statusListGetOperatable();
		if len(files) == 0:
			self.noDataSelectedCb("Revert");
			return;
		
		# filter list of files to not include externals or unversioned
		# TODO...
		
		# dump names of files to commit to another temp file
		tarFile = files.savePathsFile();
		
		# create operation dialog, and prepare it for work
		dlg = SvnOperationDialog(self, "Revert");
		dlg.setupEnv(self.branchType);
		dlg.setOp("revert");
		
		dlg.addArgs(['--targets', tarFile]); # list of files to revert
		
		# run dialog and perform operation
		dlg.go();
		dlg.exec_();
		
		# cleanup temp files
		os.remove(tarFile);
		
		# now schedule update to status list
		self.svnRefreshStatus();
	
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
			tarFile = files.savePathsFile();
			
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
			
#########################################
