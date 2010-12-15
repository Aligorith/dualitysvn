# Duality SVN
# Original Author: Joshua Leung
#
# Core includes and defines for all modules to import

####################################
# Standard Modules

import sys

import os
import shutil
import subprocess

import textwrap

####################################
# UI - PyQt

import PyQt4

from PyQt4.QtCore import *
from PyQt4.QtGui import *

####################################
# "Project" Global

from Project import *

# XXX: is this stable at all? need to verify this carefully once everything works
if len(sys.argv) > 1:
	project = DualitySettings(sys.argv[1]);
else:
	project = DualitySettings();

####################################
# Defines

# Svn Settings ----------------------

# folder names where svn keeps its meta data for the two branches
SVN_DIRNAME_BRANCH1 = ".svn"
SVN_DIRNAME_BRANCH2 = "_svn"

# environment variable that is set to allow this behaviour to work
SVN_HACK_ENVVAR = 'SVN_ASP_DOT_NET_HACK';

# Branch Type ----------------------

class BranchType:
	TYPE_TRUNK, TYPE_TRUNK_REF, TYPE_BRANCH = range(3);

####################################
