# Duality SVN
# Original Author: Joshua Leung
#
# Svn Operation Dialog 
#  - multiple SVN (or other) process operations
#    can be queued up for consideration

from coreDefines import *

from SvnOperationProcess import *

#########################################
# Operation List Widget
# TODO: may need to move this to another file?

# Not used yet.... commented out for now
"""

# Visualise output from SVN operations as a list
# TODO: to be fully implemented!
class SvnOperationList(QTreeView):
	def __init__(self):
		super(SvnOperationList, self).__init__();
		
		# view setup settings
		self.setRootIsDecorated(False);
		self.setAlternatingRowColors(True);
		
		# model settings
		
"""
		
#########################################
# Standard Operation Dialog

class SvnOperationDialog(QDialog):
	# Instance Vars ====================================
	__slots__ = (
		# Operation -----------------------------------
		'opName',	# (str) user-visible name of the (main) operation being performed
		'status',	# (ProcessStatus.STATUS_*) 
		
		# Processes -----------------------------------
		'pQ',		# (list) process queue - processes to execute
	);
	
	# Setup ============================================
	
	# ctor
	def __init__(self, parent, opName):
		super(SvnOperationDialog, self).__init__(parent);
		
		# init status
		self.opName = opName;
		self.status = ProcessStatus.STATUS_SETUP;
		
		self.pQ = [];
		
		# toplevel stuff
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
		self.wStatus.setReadOnly(True);
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
		
	# Methods ==========================================
	
	# External Setup API -------------------------------
	
	# Add a process to the tail of the queue
	# < process: (SvnOperationProcess) an operation to queue
	def addProcess(self, process):
		# add to queue to first
		self.pQ.append(process);
		
		# hook up the new process
		process.wTarget = self.wStatus;
		process.parent = self;
		
		# output redirection callbacks
		def pushOutput(sop, line):
			# insert adds without extra line padding, then scroll to this point
			sop.wTarget.setReadOnly(False);
			
			sop.wTarget.insertPlainText(line);
			sop.wTarget.ensureCursorVisible();
			
			sop.wTarget.setReadOnly(True);
		process.handleOutputCb = pushOutput;
		
		def pushErrors(sop, line):
			# insert adds without extra line padding, then scroll to this point 
			# TODO: errors should be tagged with red-text or so...
			sop.wTarget.setReadOnly(False);
			
			sop.wTarget.insertPlainText(line);
			sop.wTarget.ensureCursorVisible();
			
			sop.wTarget.setReadOnly(True);
		process.handleErrorCb = pushErrors;
			
		# process chaining callbacks
		def procStart(sop):
			# output to the widget what operation is being started
			sop.handleOutputCb(sop, "[Starting Operation: " + sop.opName + ']\n'); 
		process.preStartCb = procStart;
		
		def procDone(sop):
			# remove process from stack of processes
			del sop.parent.pQ[0];
			
			# if didn't end with failure, try to start up next procedure
			#	- stop the process if anything else happens
			if ((sop.status == ProcessStatus.STATUS_FAILED) or 
			    (sop.parent.startHeadProcess() == False)):
				# no more processes to start, or cannot start any more, so tidy up and let user get out of here
				self.status = sop.status;
				
				self.wOk.setEnabled(True);
				self.setName();
				
		process.postEndCb = procDone;
		
	# Start running operations in this dialog, and show the dialog too if this is successful
	def go(self):
		# start running the first process on the queue
		if self.startHeadProcess():
			# update status
			self.status = ProcessStatus.STATUS_WORKING;
			self.setName();
			
			# show dialog now
			self.exec_();
		else:
			# couldn't start process as there weren't any, so complain
			QMessageBox.critical(self, 
				"Internal Error",
				"No operations registered to be performed for '%s'" % (self.opName));
		
	# Internal ---------------------------------------
	
	# Start procedure at "head" of queue
	def startHeadProcess(self):
		# sanity check
		if not self.pQ:
			return False;
			
		# go!
		self.pQ[0].startProcess();
		return True;
	
	# Set name of dialog, as displayed in the titlebar
	def setName(self):
		if self.status == ProcessStatus.STATUS_WORKING:
			self.setWindowTitle(self.opName + " in Progress... - Duality SVN");
		elif self.status == ProcessStatus.STATUS_DONE:
			self.setWindowTitle(self.opName + " Done! - Duality SVN");
		elif self.status == ProcessStatus.STATUS_CANCELLED:
			self.setWindowTitle(self.opName + " is Stopping... Cleanup in progress - Duality SVN");
		else:
			self.setWindowTitle(self.opName + " Error! - Duality SVN");
			
	# callback called when cancelling dialog
	def reject(self):
		# stop active process
		if self.pQ:
			# stop head process
			headP = self.pQ[0];
			headP.endProcess();
			
			# create new process now to just cleanup
			# - reuse environment that the last op was in
			cp = SvnOperationProcess(self, "Cancelled Operation Cleanup");
			cp.setupEnv(headP.process.processEnvironment);
			
			cp.setOp("cleanup");
			cp.addDefaultArgs();
			
			# - run modal-blocking
			print "Cancel cleanup..."
			cp.runBlocking();
			print "Cleanup done"
		
		# now, cancel the dialog using it's own version
		super(SvnOperationDialog, self).reject();

#########################################
