# = Dual SVN =
# == What ==
# A helper utility to create a new SVN branch that gets updated easily
# by having the working copy simultaneously being tagged/having
# metadata for two branches in the same SVN tree, with this duality
# being managed by this utility.
#
# == How ==
# This utility is designed for the case where you have a situation where
# you've got 2 "branches" where development is taking place: a "trunk" and
# a "development branch".
#
# Assuming you've already got a working copy of "trunk" set up, ready to be 
# branched, this utility can then be used to set up a branch in the repository
# and at the same time set up your working copy to be able to:
#	1) commit to either the branch or the trunk
#	2) recieve updates made in either the branch or the trunk with no more effort 
#	   than a "standard update" would entail
#
# == This File ==
# This file is the main script, although additional helper files are also
# generated as necessary to facilitate various processes.
#
# == Key History ==
# Original Author: Joshua Leung (aligorith@gmail.com)
# Coded: November 2010

from dualitysvn import *

##########################################
# Core Methods

import sys

import os
import shutil
import subprocess

import textwrap

# --------------------------------
# Top Level Defines

# folder names where svn keeps its meta data for the two branches
SVN_DIRNAME_BRANCH1 = ".svn"
SVN_DIRNAME_BRANCH2 = "_svn"

# environment variable that is set to allow this behaviour to work
SVN_HACK_ENVVAR = 'SVN_ASP_DOT_NET_HACK';

# --------------------------------
# OS-Level Utilities

# run some command without any shell interaction
def OSU_runCommand(cmd):
	status = os.system(cmd)
	
	if status: 
		print "Exited with Error No: ", status
		#raise "Runtime Error"

# Switch to/from secondary branch
def OSU_branch2Enable(on=True):
	if on:
		os.environ[SVN_HACK_ENVVAR] = 1;
	else:
		if HACKVAR in os.environ:
			del os.environ[SVN_HACK_ENVVAR];

# --------------------------------
# Utility Methods

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

# --------------------------------
# System Behaviour

# Setup a new branch, assuming all links are valid
# < srcdir: (str) directory where "trunk" working copy is located
# < target: (str) URL for where the branch should be created in the repository
# < branchName: (str) name of the new branch (to add to svn)
def createBranch(srcdir, target, branchName):
	# make a copy of the existing svn metadata - i.e. setup "trunk" copy as "branch2"
	#status("Setting up Working Copy Duality...")
	duplicateSvnMetadata(srcdir);
	
	# perform an "svn copy" operation to make a new branch on the repository
	# 	WC + URL = instant commit 
	#status("Branching Commit Pending...");
	cmd = 'svn co "%(sd)s" %(tar)s -m "%(cm)s"' % {'sd':srcdir, 'tar':target, 'cm':"Creating '%s' branch"%(branchName)}
	OSU_runCommand(cmd); 
	
	# change working copy to the branch now
	#status("Switching Working Copy to New Branch...");
	cmd = 'svn switch %s' % (target)
	OSU_runCommand(cmd);


###########################################
# Launch Application

app = QApplication(sys.argv)

mainWin = DualityWindow()
mainWin.show()

sys.exit(app.exec_())

###########################################
