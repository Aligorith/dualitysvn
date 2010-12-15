# Duality SVN
# Original Author: Joshua Leung
#
# SVN Low-level Mangling Functions

from coreDefines import *

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
