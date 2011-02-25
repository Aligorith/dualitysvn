# Duality SVN
# Original Author: Joshua Leung
#
# "dualitysvn" module

__name__ = 'dualitysvn'

# import core defines
from coreDefines import *

# SVN utilties - not need for all, but good to have at hand
from SvnTools import *

# import everything into here just to make things easier
# FIXME: make proper use of namespaces...
from SvnOperationProcess import *
from InternalOperationProcess import *

from SvnStatusList import *

from SvnOperationDialog import *
from SvnCommitDialog import *

from ProjectSettingsDialog import *

from MainWindow import *
