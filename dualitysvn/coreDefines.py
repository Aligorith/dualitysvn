# Duality SVN
# Original Author: Joshua Leung
#
# Core includes and defines for all modules to import

####################################
# Standard Modules

import sys
import os

####################################
# UI - PyQt

from PyQt4.QtCore import *
from PyQt4.QtGui import *

####################################
# Own includes for use everywhere

from SvnTools import *

####################################
# "Project" Global

from Project import DualitySettings

# XXX: is this stable at all? need to verify this carefully once everything works
if len(sys.argv) > 1:
	project = DualitySettings(sys.argv[1]);
else:
	project = DualitySettings();

####################################
# Defines

# Duality Constants -----------------

DUALITY_VERSION_STRING = "0.1"

# Svn Settings ----------------------

# folder names where svn keeps its meta data for the two branches
SVN_DIRNAME_BRANCH1 = ".svn"
SVN_DIRNAME_BRANCH2 = "_svn"

# environment variable that is set to allow this behaviour to work
SVN_HACK_ENVVAR = 'SVN_ASP_DOT_NET_HACK';

# Branch Type -------------------------

class BranchType:
	TYPE_TRUNK, TYPE_TRUNK_REF, TYPE_BRANCH = range(3);
	
# Status Messages for Processes -------

class ProcessStatus:
	STATUS_SETUP, STATUS_WORKING, STATUS_DONE, STATUS_FAILED, STATUS_CANCELLED = range(5);

####################################
