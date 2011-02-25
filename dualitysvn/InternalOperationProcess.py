# Duality SVN
# Original Author: Joshua Leung
# 
# Base support for Internal Operations wrapped for use alongside 
# external SVN processes

from coreDefines import *

####################################
# Output Buffer
#
# Stores output produced by process, returning it 
# as required by the end user

class ProcessOutputBuffer:
	__slots__ = (
		'archive',		# (list) output that has already been read from the buffer
		'latest'		# (list) output that has just been added to the buffer but not yet read
	);
	
	def __init__(self):
		# init internal buffers
		self.archive = [];
		self.latest = [];
		
	# Add some text to the "unread" buffer
	def append(self, text):
		self.latest.append(text);
		
	# Checks if there is any content in the buffer to read
	def canReadLine(self):
		return len(self.latest) != 0;
		
	# "Read" a line from the buffer, returning the line as a string for further usage
	def readLine(self):
		# move first line from start of "latest" to tail of "archive"
		line = latest[0];
		
		del latest[0];
		archive.append(line);
		
		return line;

####################################
# ThreadAsFauxProcess
#
# This wrapper allows threads (running py-coded operations) to be
# used alongside external processes being run through QProcess,
# with a seamless interface emulating the behaviour of the latter.
#
# To use:
# 	- subclass and reimplement the run() method
#	- use the write(out_txt) and error(err_txt) methods to produce any output
#	- call done(exitCode) method run() method is done

class ThreadAsFauxProcess(QThread):
	__slots__ = (
		'_state',		# (QProcess.ProcessState)
		'_exitCode',	# (int)
		'_exitStatus',	# (QProcess.ExitStatus)
		
		'_outBuf',		# (ProcessOutputBuffer) 
		'_errBuf',		# (ProcessOutputBuffer)
		'_bufChannel',	# (QProcess.ProcessChannel) which one of these readers we use
	);
	
	# Setup ================================================================
	
	def __init__ (self, func_op):
		# initialise owner stuff
		QThread.__init__(self)
		
		# "starting" state = not yet started, but being prepared to be started
		self._state = QProcess.Starting;
		
		# "output" buffers
		self._outBuf = ProcessOutputBuffer();
		self._errBuf = ProcessOutputBuffer();
		
	# QProcess API =========================================================
		
	# QProcess-style "state" polling
	# TODO: there needs to be something to check for when the process ends...
	def state(self):
		return self._state;
		
	# QProcess-style "start", which is a wrapper around QThread.start()
	def start(self, args):
		try:
			# set runtime arguments
			self.args += list(args);
			
			# now, try to start the thread now
			QThread.start(self);
			self._state = QProcess.Running;
		except RuntimeException:
			# thread is already running
			self._state = QProcess.NotRunning;
			
	# QProcess-style "kill"
	def kill(self):
		# nasty, but the closest we can get to kill a process is to terminate the thread
		self.terminate();
		self._state = QProcess.NotRunning;
		
	# QProcess-style "run blocking"
	def waitForFinished(self, dummyArg):
		# start the thread
		self.start();
		
		# the default args give this no timeouts
		#	- this will return true/false. True is also return if thread is already done
		return self.wait();
		
	# ---------------------------------------------
	
	# QProcess.exitCode() : int
	def exitCode(self):
		return self._exitCode;
		
	# QProcess.exitStatus() : QProcess.ExitStatus
	def exitStatus(self):
		return self._exitStatus;
	
	# ---------------------------------------------
	
	# Get the ProcessOutputBuffer to retrieve output from
	# (Internal Helper)
	def getReadBuffer(self):
		if self._bufChannel == QProcess.StandardError:
			return self._errBuf;
		else:
			return self._outBuf;
	
	# QProcess-style changing read buffer
	# < channel: (QProcess.ProcessChannel)
	def setReadChannel(self, channel):
		self._bufChannel = channel;
	
	# QProcess-style checking output buffer for more content
	def canReadLine(self):
		return self.getReadBuffer().canReadLine();
		
	# QProcess-style "readLine" (to get single "line" of content from the text buffer)
	def readLine(self):
		return self.getReadBuffer().readLine();
	
	# QThread API ===========================================================
	
	# QThread.run() - this is where the bulk of things go
	def run(self):
		# templates for standard out output
		self.write("Some text\n");
		self.error("Houston, we have a problem!\n");
		
		# ... own operations - may contain the templates above ...
		
		# when done, we must notify the owner
		self.done(0, QProcess.NormalExit);
		#self.done(-1, QProcess.CrashExit);
		
	# Own Wrapping API =======================================================
	
	# Output from operation - cues up relevant Qt signals...
	def write(self, text):
		# add line to our output-text buffer
		self._outBuf.append(text);
		
		# Qt-signal
		self.emit(SIGNAL('readyReadStandardOutput()'));
		
	# Error output from operation - cues up relevant Qt signals...
	def error(self, text):
		# add line to our error-text buffer
		self._errBuf.append(text);
		
		# Qt-signal
		self.emit(SIGNAL('readyReadStandardError()'));
		
	# Operation done - cues up relevant Qt signals
	# < exitCode: (int) 0 for normal exit, non-zero otherwise
	# < exitStatus: (QProcess.ExitStatus)
	def done(self, exitCode, exitStatus):
		# store exit code/status for retrieval later
		self._exitCode = exitCode;
		self._exitStatus = exitStatus;
		
		# Qt-signal
		self.emit(SIGNAL('finished(int)'), exitCode);

####################################
# InternalOperationProcess
#
# This wrapper allows functions to get run as if they were processes
# though this ends up being run in a blocking manner

# ! Keep this in sync with SvnOperationProcess

####################################
