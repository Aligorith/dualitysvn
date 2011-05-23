# Duality SVN
# Original Author: Joshua Leung
#
# SVN Operation - A Wrapper for QProcess to perform SVN operations

from coreDefines import *

from AbstractOperationProcess import *

#########################################
# Operation Object

# TODO:
#	- progress % tracker + callbacks for determining this

class SvnOperationProcess(AbstractOperationProcess):
	__slots__ = (
		# SVN Settings --------------------
		'svnOp',	# (str) name of svn subcommand to use
		'args',		# (list<str>) list of argument strings to use
		'tarList',	# (SvnStatusDatalist) list of targets to use
	);
	
	# Internal Setup ==============================
	
	# setup "process" for grabbing stuff from
	def __init__(self, parent, name):
		# init generic stuff
		super(SvnOperationProcess, self).__init__(parent, name);
		
		# init own vars
		self.svnOp = "";
		self.args = ["--non-interactive", "--trust-server-cert"]; # no prompts or stopping for anything!
		self.tarList = None; # optional "list of targets"
	
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
		
	# Add a list of default arguments to be passed to svn for this operation (using internal svnOp name)
	def addDefaultArgs(self):
		self.args += SvnOp_Args[self.svnOp];
		
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
	
	# Callbacks =================================
	
	# Internal method for starting the process 
	# Overrides the basic stub in the abstract baseclass
	def _start(self):
		# setup targets list (if needed)
		if self.tarList:
			tarFileN = self.tarList.savePathsFile(self.svnOp);
			tarArgs = ['--targets', tarFileN];
			print "saved targets list to '%s'" % (tarFileN)
		else:
			tarArgs = [];
		
		# try and start the process now
		self.process.start("svn", [self.svnOp]+self.args+tarArgs);
		
	# Cleanup for changes done internally
	# Overrides version in abstract baseclass to include support for cleaning up targets list
	def doneProcess(self):
		# cleanup targets list temp file (if needed)
		if self.tarList:
			try:
				tarFile = self.tarList.getPathsFileName(self.svnOp);
				os.remove(tarFile);
			except:
				# file may already have been removed
				print "targets list already removed? - '%s'" % (tarFile)
				pass;
		
		# now run the standard version
		super(SvnOperationProcess, self).doneProcess();

#########################################
