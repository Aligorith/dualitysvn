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

# Branch Type ----------------------

class BranchType:
	TYPE_TRUNK, TYPE_TRUNK_REF, TYPE_BRANCH = range(3);

####################################
