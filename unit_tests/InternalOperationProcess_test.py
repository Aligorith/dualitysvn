# Quick test script testing whether internal operation process actually works

from dualitysvn.coreDefines import *

from dualitysvn.SvnOperationDialog import *
from dualitysvn.InternalOperationProcess import *

########################################
# Thread Object

# a thread to act as a process from which we grab output from
# NOTE: internally, should convert all newlines to format required...
class TestThreadProcess(ThreadAsFauxProcess):
	def run(self):
		self.error("> Starting thread:\r\n")
		for x in range(30):
			self.write("\t%d\r\n" % (x))
		self.error("> Thread done\r\n")
		self.done(0)

########################################
# Setup UI for testing this

app = QApplication(sys.argv)

# dialog for showing the progress of this process
# (this is where this output should ultimately get hooked up to be shown, so it should work too)
dlg = SvnOperationDialog(None, "Internal Operation Process Test");

# instantiate this process
p1 = InternalOperationProcess(dlg, "Test thread", TestThreadProcess());
dlg.addProcess(p1);

dlg.accept = lambda: sys.exit(0);

# run everything
dlg.go();

#sys.exit(app.exec_())
 