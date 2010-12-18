# Duality SVN
# Original Author: Joshua Leung
#
# SVN Operation - A Wrapper for QProcess to perform SVN operations

from coreDefines import *

#########################################
# Operation Object

# TODO:
#	- progress % tracker + callbacks for determining this

class SvnOperationProcess:
	__slots__ = (
		# Process -------------------------
		'process',	# (QProcess) process to operate
		
		'status', 	# (ProcessStatus.STATUS_*) state of the proces
		
		# Affected Widgets ----------------
		'wStart',	# (QPushButton) button used to start process
		'wEnd',		# (QPushButton) button used to abort process
		
		'wTarget',	# (QWidget) widget where results may be sent, OR
		'model',	# object where data may go 
		'parent',	# (QWidget?) widget or standard object that this was called from
		
		# Widget Settings -----------------
		'widgetVisibility',	# (bool) toggle visibility of widgets instead of enabled status (if widgets available)
		
		'silentErrors',		# (bool) don't broadcast errors with msgboxes
		
		# SVN Settings --------------------
		'opName',	# (str) user-visible name of action we're doing
		
		'svnOp',	# (str) name of svn subcommand to use
		'args',		# (list<str>) list of argument strings to use
		'tarList',	# (SvnStatusDatalist) list of targets to use
		
		# Callbacks -----------------------
		'handleOutputCb',	# (fn(SvnOperationProcess, line:str)) handle line of output from process, for adding to model/target widget as needed
		'handleErrorCb',	# (fn(SvnOperationProcess, line:str)) handle line of error output from process
		
		'preStartCb',		# (fn(SvnOperationProcess)) operation to perform before starting process
		'postEndCb'			# (fn(SvnOperationProcess)) operation to perform after process finished
	);
	
	# Internal Setup ==============================
	
	# setup "process" for grabbing stuff from
	def __init__(self, parent, name):
		# null-define other data first
		self.status = ProcessStatus.STATUS_SETUP;
		
		self.wStart = self.wEnd = None;
		self.widgetVisibility = False;
		
		self.silentErrors = False; # errors are shown as msgboxes
		
		self.wTarget = None;
		self.model = None;
		self.parent = parent;
		
		self.opName = name;
		self.svnOp = "";
		self.args = ["--non-interactive", "--trust-server-cert"]; # no prompts or stopping for anything!
		self.tarList = None; # optional "list of targets"
		
		# null-define the callbacks that users can bind
		self.handleOutputCb = None;
		self.handleErrorCb = None;
		
		self.preStartCb = None;
		self.postEndCb = None;
		
		# setup process
		self.setupProcess();
		
	# setup process and its general callbacks 
	def setupProcess(self):
		# create process object - reuse for every instance...
		self.process = QProcess();
		
		# attach callbacks
		# XXX: err...
		self.parent.connect(self.process, SIGNAL("readyReadStandardOutput()"), self.readOutput);
		self.parent.connect(self.process, SIGNAL("readyReadStandardError()"), self.readErrors);
		self.parent.connect(self.process, SIGNAL("finished(int, QProcess::ExitStatus)"), self.processEnded);
	
	# External Setup API ========================
	
	# Svn Command -------------------------------
	
	# Set the svn operation that needs to be performed
	# < svnOpName: (str) name of the operation (i.e. commit,up,etc.) to perform using svn
	def setOp(self, svnOpName):
		self.svnOp = svnOpName;
	
	# Add a list of arguments to be passed to svn when running it
	# < args: (list<str>) list of arguments to run
	def addArgs(self, args):
		self.args += args;
		
	# Set the list of targets for the operation to use
	# < targetsList: (SvnStatusDatalist) list of paths that need to be operated on
	def setTargets(self, targetsList):
		self.tarList = targetsList;
		
	# Environment --------------------------------
	
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
			
	# Process Control -------------------------------
	
	# set start/end widgets, and connect them
	def setControlWidgets(self, start, end):
		# set widgets
		self.wStart = start;
		self.wEnd = end;
		
		# connect them to our methods
		# NOTE: only end needs to be hooked up for now, since start will create this object usually...
		self.wEnd.clicked.connect(self.endProcess);
	
	# Callbacks =================================
	
	# Exposed API -------------------------------
	
	# Start Process 
	def startProcess(self):
		# perform pre-start operation
		if self.preStartCb:
			self.preStartCb(self);
		
		# setup targets list (if needed)
		if self.tarList:
			tarFileN = self.tarList.savePathsFile(self.svnOp);
			tarArgs = ['--targets', tarFileN];
		else:
			tarArgs = [];
		
		# try and start the process now
		self.process.start("svn", [self.svnOp]+self.args+tarArgs);
		
		if self.process.state() == QProcess.NotRunning:
			# msgbox warning about error if not silent
			if not self.silentErrors:
				QMessageBox.warning(self.parent,
					"SVN Error",
					"Could perform %s operation" % (self.opName));
					
			# set to "failed" status
			self.status = self.status = ProcessStatus.STATUS_FAILED;
		else:
			# disable start + enable stop buttons (if given)
			if self.wStart and self.wEnd:
				if self.widgetVisibility:
					# switch the visible widget - assume that both will be showable
					self.wStart.setVisible(False);
					self.wEnd.setVisible(True);
				else:
					# switch the enabled widget
					self.wStart.setEnabled(False);
					self.wEnd.setEnabled(True);
					
			# set to "running" status
			self.status = ProcessStatus.STATUS_WORKING;
		
	# Abort process prematurely
	def endProcess(self):
		# kill process - only way to get rid of console apps on windows
		self.process.kill();
		
		# FIXME: should we have a "status killed"?
		self.status = ProcessStatus.STATUS_DONE;
		
		# refresh
		self.doneProcess();
	
	# Run process in a blocking manner (for background helper-processes)
	def runBlocking(self):
		# start running
		# TODO: should we add return bool to this to check successs?
		self.startProcess();
		
		# this will return when the process is done at last
		# 	-1 arg gives "no-timeout"
		return self.process.waitForFinished(-1);
	
	# Internal (Reading) ------------------------
	
	# read output messages from process
	def readOutput(self):
		line = str(self.process.readLine()).rstrip("\n");
		
		# output
		if self.handleOutputCb:
			self.handleOutputCb(self, line);
		else:
			print "StdOut>>", line
	
	# read error messages from process
	def readErrors(self):
		# switch to stderr channel to read, then switch back
		self.process.setReadChannel(QProcess.StandardError);
		
		line = str(self.process.readLine()).rstrip("\n");
		
		if self.handleErrorCb:
			self.handleErrorCb(self, line);
		else:
			print "StdErr>>", line
		
		self.process.setReadChannel(QProcess.StandardOutput);
		
	# Internal (Running) ------------------------
		
	# Cleanup for changes done internally
	def doneProcess(self):
		# reenable start + enable stop buttons (if given)
		if self.wStart and self.wEnd:
			if self.widgetVisibility:
				# switch the visible widget - assume that both will be showable
				self.wStart.setVisible(True);
				self.wEnd.setVisible(False);
			else:
				# switch the enabled widget
				self.wStart.setEnabled(True);
				self.wEnd.setEnabled(False);
		
		# cleanup targets list temp file (if needed)
		if self.tarList:
			tarFile = self.tarList.getPathsFileName(self.svnOp);
			os.remove(tarFile);
		
		# run cleanup callback
		if self.postEndCb:
			self.postEndCb(self);
		
	# callback called when svn operation process ends
	def processEnded(self, exitCode, exitStatus):
		# grab rest of output
		while self.process.canReadLine():
			self.readOutput();
		
		# TODO: grab rest of errors?
		
		# if exited with some problem, make sure we warn
		# TODO: also keep track of other status too...
		if exitStatus == QProcess.CrashExit:
			# broadcast error with a msgbox?
			if not self.silentErrors:
				QMessageBox.warning(self.parent,
					"SVN Error",
					"%s operation was not completed successfully" % (self.opName));
					
			# set status to failed
			self.status = ProcessStatus.STATUS_FAILED;
		else:
			# succeeded
			self.status = ProcessStatus.STATUS_DONE;
		
		# done cleanup
		self.doneProcess();

#########################################
