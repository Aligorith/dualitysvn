# Duality SVN
# Original Author: Joshua Leung
#
# SVN Low-level Mangling Functions

from coreDefines import *

import shutil

#######################################
# Branch Setup Utilities

# Duplicate all ".svn" folders (and their contents) to "_svn" ones recursively
# - Used for setting up local copy of branch
#
# < root: (str) path to directory where root of source tree resides
# > return[0]: (list) summary of errors that occurred during this process (description+path)
def duplicateSvnMetadata(root):
	# error stack
	errors = [];
	
	# traverse directory tree
	# 	- p: (str) path of the current directory being traversed
	#	- d: (list<str>) names of directories in current directory being traversed
	#	- f: (list<str>) names of files in current directory
	for p,d,f in os.walk(root):
		# at each directory level, we can perform a copy if the data is present
		# BUT we mustn't ever enter one of these subdirs that we're handling
		if SVN_DIRNAME_BRANCH1 in d:
			d.remove(SVN_DIRNAME_BRANCH1);
			
			# we have a target directory to copy, so copy it
			shutil.copytree(os.path.join(p, SVN_DIRNAME_BRANCH1), os.path.join(p, SVN_DIRNAME_BRANCH2));
		elif SVN_DIRNAME_BRANCH2 in d:
			d.remove(SVN_DIRNAME_BRANCH2);
			
			# only target directory exists, so we've got an error
			errors.append(("Path only has target directory. Inconsistent repository copy.", p));
		else:
			# data not present... skip this directory
			pass;
			
	# return list of errors
	return errors;

#######################################
# SVN Operation Argument Defines

# svn opname : 
#	[list, of, arguments,
#	 for, each, operation]

SvnOp_Args = {
	# Target-less -----------------------------------
	'status' :
		['--ignore-externals'], # 'externals' are other SVN trees linked in. They DON'T REALLY MATTER FOR ANYTHING!
		
	'update' :
		['--accept', 'postpone'], 	# easiest conflict resolution method still is to manually fix in text editor 
		
	'checkout' :
		['--force'],		# don't let conflict-errors abort the operation
	
	# With Target List ------------------------------
	
	'add' :
		['--auto-props'],	# SVN props are automatically added based on filetype
		
	'delete' :
		[],
		#['--keep-local'],	# don't delete working copy's copy (TODO: enable this when branched so that we can do the other branch next)
		
	'revert' :
		[],
		
	'commit' :
		['--force-log',
		 #'-F', LOGFILE		# <--- these are added manually by commit code
		],
		
	'cleanup' :
		[],
		
	'diff' :
		[],
		
	'resolved' :
		[]
};

#######################################
