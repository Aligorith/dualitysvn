# Duality SVN
# Original Author: Joshua Leung
#
# Abstract Operation Process - base-class for wrappers
# around QProcess-like interfaces for running external
# or internal operations under a common framework

from coreDefines import *

from abc import *

#########################################
# Operation Object

class AbstractOperationProcess:
	__metaclass__ = ABCMeta
	
	__slots__ = (
		# Process -------------------------
		'process',	# (QProcess) process to operate
		
		'status', 	# (ProcessStatus.STATUS_*) state of the process
		
		'opName',	# (str) user-visible name of action we're doing
		
		# Affected Widgets ----------------
		'wStart',	# (QPushButton) button used to start process
		'wEnd',		# (QPushButton) button used to abort process
		
		'wTarget',	# (QWidget) widget where results may be sent, OR
		'model',	# object where data may go 
		'parent',	# (QWidget?) widget or standard object that this was called from
		
		# Widget Settings -----------------
		'widgetVisibility',	# (bool) toggle visibility of widgets instead of enabled status (if widgets available)
		
		'silentErrors',		# (bool) don't broadcast errors with msgboxes
		
		# Callbacks -----------------------
		'handleOutputCb',	# (fn(SvnOperationProcess, line:str)) handle line of output from process, for adding to model/target widget as needed
		'handleErrorCb',	# (fn(SvnOperationProcess, line:str)) handle line of error output from process
		
		'preStartCb',		# (fn(SvnOperationProcess)) operation to perform before starting process
		'postEndCb'			# (fn(SvnOperationProcess)) operation to perform after process finished
	);
	
	# Internal Setup ==============================
	
	# setup "process" for grabbing stuff from
	def __init__(self, parent, name, process=None):
		# null-define other data first
		self.status = ProcessStatus.STATUS_SETUP;
		
		self.wStart = self.wEnd = None;
		self.widgetVisibility = False;
		
		self.silentErrors = False; # errors are shown as msgboxes
		
		self.wTarget = None;
		self.model = None;
		self.parent = parent;
		
		self.opName = name;
		
		# null-define the callbacks that users can bind
		self.handleOutputCb = None;
		self.handleErrorCb = None;
		
		self.preStartCb = None;
		self.postEndCb = None;
		
		# setup process
		self.setupProcess(process);
		
	# setup process and its general callbacks 
	def setupProcess(self, process):
		# create or store link to proces object
		if process is not None:
			self.process = process;
		else:
			self.process = QProcess();
		
		# attach callbacks
		# XXX: err...
		self.parent.connect(self.process, SIGNAL("readyReadStandardOutput()"), self.readOutput);
		self.parent.connect(self.process, SIGNAL("readyReadStandardError()"), self.readErrors);
		self.parent.connect(self.process, SIGNAL("finished(int, QProcess::ExitStatus)"), self.processEnded);
		self.parent.connect(self.process, SIGNAL("finished(int)"), self.processEnded);
	
	# External Setup API ========================
	
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
		
		# try and start the process now
		self._start();
		
		if self.process.state() == QProcess.NotRunning:
			# msgbox warning about error if not silent
			if not self.silentErrors:
				QMessageBox.warning(self.parent,
					"Operation Error",
					"Could not perform %s operation" % (self.opName));
					
			# set to "failed" status
			self.status = ProcessStatus.STATUS_FAILED;
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
		# sanity check: only need to do this for "running" processes
		if self.status != ProcessStatus.STATUS_WORKING:
			return;
		
		# kill process - only way to get rid of console apps on windows
		self.process.kill();
		self.status = ProcessStatus.STATUS_CANCELLED;
		
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
	def readErrors(self, needsSwap=True):
		# switch to stderr channel to read, then switch back
		if needsSwap:
			self.process.setReadChannel(QProcess.StandardError);
		
		line = str(self.process.readLine()).rstrip("\n");
		
		if self.handleErrorCb:
			self.handleErrorCb(self, line);
		else:
			print "StdErr>>", line
		
		if needsSwap:
			self.process.setReadChannel(QProcess.StandardOutput);
		
	# read rest of output from process
	def readRemaining(self):
		# standard output
		while self.process.canReadLine():
			self.readOutput();
			
		# standard error
		# 	-  need to change read channel so that we can read this 
		self.process.setReadChannel(QProcess.StandardError);
		
		while self.process.canReadLine():
			self.readErrors(False);
		
		self.process.setReadChannel(QProcess.StandardOutput);
		
	# Internal (Running) ------------------------
		
	# Internal method for starting the process
	# ! To be implemented by subclasses
	@abstractmethod
	def _start(self):
		# 1) perform any extra + necessary tasks before starting
		# e.g. set up targets list
		
		# 2) actually start the process
		self.process.start(); # dummy example call...
		
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
		
		# run cleanup callback
		if self.postEndCb:
			self.postEndCb(self);
		
	# callback called when svn operation process ends
	def processEnded(self, exitCode, exitStatus=QProcess.NormalExit):
		# grab rest of output
		self.readRemaining();
		
		# if exited with some problem, make sure we warn
		if (exitStatus == QProcess.CrashExit) or (self.process.exitCode() != 0):
			# broadcast error with a msgbox?
			if not self.silentErrors:
				QMessageBox.warning(self.parent,
					"Operation Error",
					"%s operation was not completed successfully" % (self.opName));
					
			# set status to failed
			self.status = ProcessStatus.STATUS_FAILED;
		else:
			# succeeded
			self.status = ProcessStatus.STATUS_DONE;
		
		# done cleanup
		self.doneProcess();

#########################################

#########################################
