# Duality SVN
# Original Author: Joshua Leung
#
# Svn Operation Dialog - Run some svn command

from coreDefines import *

#########################################
# Operation List Widget
# TODO: may need to move this to another file?

# Visualise output from SVN operations as a list
# TODO: to be fully implemented!
class SvnOperationList(QTreeView):
	def __init__(self):
		super(SvnOperationList, self).__init__();
		
		# view setup settings
		self.setRootIsDecorated(False);
		self.setAlternatingRowColors(True);
		
		# model settings

#########################################
# Standard Operation Dialog

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
		# NOTE: these common options rule out any error prompts that might otherwise come up
		self.args = ['--non-interactive', '--trust-server-cert']; 
		
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
		useSecondaryBranch = (branchType == BranchType.TYPE_TRUNK_REF); 
		
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
		
		self.wStatus.insertPlainText(line);
		self.wStatus.ensureCursorVisible();
	
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
		# grab rest of output
		while self.process.canReadLine():
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

#########################################
