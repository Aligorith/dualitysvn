# Duality SVN
# Original Author: Joshua Leung
#
# Branch Pane - Panel representing the main UI for a branch

# import all from "dualitysvn" package
from . import *

#########################################
# Branch Operations Panel

# Panel for day to day operations within a "branch"
class BranchPanel(QWidget):
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
		super(BranchPanel, self).__init__();
		
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
		self.wUrl = QLineEdit();
		self.wUrl.setPlaceholderText("e.g. https://svnroot/project/my-branch");
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
		#self.wStopRefreshStatus.clicked.connect(self.stopRefreshStatus); # NOTE: this is bound by the process as needed
		
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
			if project.urlTrunk:
				self.wUrl.setText(project.urlTrunk);
			else:
				self.wUrl.setText("");
			self.wUrl.setReadOnly(False);
		
		# clear status list
		self.wStatusView.model.clearAll();
		self.updateActionWidgets();
	
	# change the type of branch
	def changeBranchType(self, newType):
		# set type after validation
		if not newType in (BranchType.TYPE_BRANCH, BranchType.TYPE_TRUNK_REF, BranchType.TYPE_TRUNK):
			raise ValueError, "Not a valid type of branch - %d" % newType;
		elif newType == self.branchType:
			return; # no changes needed, so don't do refresh
		else:
			self.branchType = newType;
		
		# do updates
		self.updateProjectWidgets();
	
	# Working Copy Import ----------------------------------------------------
	
	def svnUpdate(self):
		# setup process
		p1 = SvnOperationProcess(self, "Update");
		p1.setupEnv(self.branchType);
		
		p1.setOp("update");
		p1.addDefaultArgs();
		
		# setup and run dialog
		dlg = SvnOperationDialog(self, "Update");
		
		dlg.addProcess(p1);
		
		dlg.go();
		
	
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
		# setup svn process
		self.refreshProcess = rp = SvnOperationProcess(self, "Refresh Status");
		rp.setupEnv(self.branchType);
		
		rp.setOp("status");
		rp.addDefaultArgs();
		
		rp.setControlWidgets(self.wRefreshStatus, self.wStopRefreshStatus);
		rp.wTarget = self.wStatusView;
		rp.model = self.wStatusView.model;
		
		rp.widgetVisibility = True; # allow cancelling operation by showing wStopRefreshStatus
		
		# setup callbacks
		#	pre-start ..................
		def setup(sop):
			# start fresh
			sop.model.clearAll();
			
			# we could be here a while
			sop.parent.updateActionWidgets(); 
		rp.preStartCb = setup;
		
		# 	done .......................
		def done(sop):
			# hack: force sorting to be performed again now
			sop.wTarget.setSortingEnabled(True);
			
			# update with new status
			sop.parent.updateActionWidgets();
		rp.postEndCb = done;
		
		# 	get items..................
		def store(sop, line):
			# parse the output to create a new line, and add to model
			if len(line):
				item = SvnStatusListItem(line);
				sop.model.add(item);
		rp.handleOutputCb = store;
		
		# go!
		rp.startProcess();
	
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
		
		# setup process
		p1 = SvnOperationProcess(self, "Add");
		p1.setupEnv(self.branchType);
		
		p1.setOp("add");
		p1.addDefaultArgs();
		p1.setTargets(files);
		
		# setup and run dialog
		dlg = SvnOperationDialog(self, "Add");
		
		dlg.addProcess(p1);
		
		dlg.go();
		
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
		
		# setup process
		# TODO: what happens for the other branch?
		p1 = SvnOperationProcess(self, "Delete");
		p1.setupEnv(self.branchType);
		
		p1.setOp("delete");
		p1.addDefaultArgs();
		p1.setTargets(files);
		
		# setup and run dialog
		dlg = SvnOperationDialog(self, "Delete");
		
		dlg.addProcess(p1);
		
		dlg.go();
		
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
		
		# setup process
		p1 = SvnOperationProcess(self, "Revert");
		p1.setupEnv(self.branchType);
		
		p1.setOp("revert");
		p1.addDefaultArgs();
		p1.setTargets(files);
		
		# setup and run dialog
		dlg = SvnOperationDialog(self, "Revert");
		
		dlg.addProcess(p1);
		
		dlg.go();
		
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
			
			# setup process
			p1 = SvnOperationProcess(self, "Commit");
			p1.setupEnv(self.branchType);
			
			p1.setOp("commit");
			p1.addDefaultArgs();
			p1.addArgs(['--force-log', '-F', logFile]); # log message - must have one
			p1.setTargets(files);
			
			# setup and run dialog
			dlg2 = SvnOperationDialog(self, "Commit");
			
			dlg2.addProcess(p1);
			
			dlg2.go();
			
			# cleanup temp files
			os.remove(logFile);
			
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
