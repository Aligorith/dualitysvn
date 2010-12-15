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

###########################################
# Launch Application

app = QApplication(sys.argv)

mainWin = DualityWindow()
mainWin.show()

sys.exit(app.exec_())

###########################################
