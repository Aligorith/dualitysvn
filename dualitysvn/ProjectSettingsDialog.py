# Duality SVN
# Original Author: Joshua Leung
#
# Project Settings Dialog

from coreDefines import *

#########################################
# Project Settings Dialog

class ProjectSettingsDialog(QDialog):
	# Setup ============================================
	
	# ctor
	def __init__(self, parent):
		super(ProjectSettingsDialog, self).__init__(parent);
		
		# toplevel stuff
		self.setWindowTitle("Project Settings");
		#self.setGeometry(150, 150, 600, 300);
		
		# setup UI
		self.layout = QVBoxLayout();
		self.setLayout(self.layout);
		
		self.setupUI();
		
	# main widget setup
	def setupUI(self):
		# 1) temp file directory ..........................................
		gb = QGroupBox("Temporary Files");
		self.layout.addWidget(gb);
		
		grp = QGridLayout();
		gb.setLayout(grp);
		
		# 1.1) directory label
		grp.addWidget(QLabel("Directory:"), 1,1); # r1 c1
		
		# 1.2) directory field
		# TODO: setup red-highlight when directory doesn't exist!
		if project.tempFilesDir:
			self.wDirectory = QLineEdit(project.tempFilesDir);
		else:
			self.wDirectory = QLineEdit();
		self.wDirectory.setToolTip("Directory where working copy is located");
		self.wDirectory.setPlaceholderText("e.g. ./tmp/");
		self.wDirectory.setFocusPolicy(Qt.ClickFocus); # it shouldn't gain focus by itself or through tabbing!
		
		self.wDirectory.textChanged.connect(self.setTempFilesDir);
		
		grp.addWidget(self.wDirectory, 1,2); # r1 c2
		
		# 1.2) browse-button for directory widget
		self.wDirBrowseBut = QPushButton("Browse...");
		self.wDirBrowseBut.setFocusPolicy(Qt.NoFocus); # it shouldn't gain focus by itself or through tabbing!
		
		self.wDirBrowseBut.clicked.connect(self.tempDirBrowseCb);
		
		grp.addWidget(self.wDirBrowseBut, 1,3); # r1 c3
		
		# space ........
		self.layout.addSpacing(20);
		
		# 2) Local Modifications List .......................................
		
		gb = QGroupBox("Local Only Modifications");
		self.layout.addWidget(gb);
		
		grp = QGridLayout();
		gb.setLayout(grp);
		
		# 2.1) Add new local modification
		# 2.1.1) Text-field for defining new item to add
		self.wSkipListNewItem = QLineEdit();
		self.wSkipListNewItem.setPlaceholderText("e.g. relative/path/to/directory_or_file_to_ignore");
		
		self.wSkipListNewItem.textChanged.connect(self.validateNewSkipPathLength);
		self.wSkipListNewItem.returnPressed.connect(self.skiplistAdd);
		
		grp.addWidget(self.wSkipListNewItem, 1,1, 1,3); # r1 c1, h1 w3
		
		# 2.1.2) Add button for adding new item
		self.wSkipListAdd = QPushButton("+");
		self.wSkipListAdd.setToolTip("Add new path to ignore as 'local only' modification (existing files in under version control will not get committed over)");
		self.wSkipListAdd.setEnabled(False);
		
		self.wSkipListAdd.clicked.connect(self.skiplistAdd);
		
		grp.addWidget(self.wSkipListAdd, 1,4, 1,1); # r1 c4, h1 w1
		
		# 2.2) skip-list (list of local modifications)
		# XXX: for now, we'll just use the classic-style lists to save ourselves some work
		# since this list will be the only way of editing the skiplist while this dialog is open
		self.wSkipListView = QListWidget();
		self.wSkipListView.setSelectionMode(QAbstractItemView.ExtendedSelection);
		
			# populate this list from the projects list 
		for skipItem in project.skiplist:
			self.wSkipListView.addItem(skipItem);
		
		grp.addWidget(self.wSkipListView, 2,1, 1,4); # r2 c1, h1 w4
		
		# 2.3) commands...
		# 2.3.1) toggle all
		self.wSkipListToggleSel = QPushButton("Toggle All");
		self.wSkipListToggleSel.setToolTip("Toggle selection of all paths in list of 'local only' modifications");
		self.wSkipListToggleSel.setFocusPolicy(Qt.NoFocus); # it shouldn't gain focus by itself or through tabbing!
		
		self.wSkipListToggleSel.clicked.connect(self.skiplistToggleSel);
		
		grp.addWidget(self.wSkipListToggleSel, 3,1, 1,1); # r3 c1, h1 w1
		
		# 2.3.2) remove selected
		self.wSkipListRemove = QPushButton("Remove");
		self.wSkipListRemove.setToolTip("Remove selected paths from list of 'local only' modifications");
		self.wSkipListRemove.setFocusPolicy(Qt.NoFocus); # it shouldn't gain focus by itself or through tabbing!
		
		self.wSkipListRemove.clicked.connect(self.skiplistRemove);
		
		grp.addWidget(self.wSkipListRemove, 3,4, 1,1); # r3 c4, h1 w1
		
		# space ........
		self.layout.addSpacing(20);
		
		# X) close button ................................
		
		grp = QDialogButtonBox();
		self.layout.addWidget(grp);
		
		self.wClose = grp.addButton("Close", QDialogButtonBox.RejectRole);
		self.wClose.setFocusPolicy(Qt.NoFocus); # it shouldn't gain focus by itself or through tabbing!
		self.wClose.clicked.connect(self.reject);
		
	# Callbacks ========================================
	
	# Temp Files ---------------------------------------
	
	# Temp files directory browse callback
	def tempDirBrowseCb(self):
		if not project.tempFilesDir:
			project.tempFilesDir = ".";
		
		# get new directory
		newDir = QFileDialog.getExistingDirectory(self, "Open Directory",
			project.tempFilesDir,
			QFileDialog.ShowDirsOnly
			| QFileDialog.DontResolveSymlinks);
		
		# set this directory
		if newDir:
			self.wDirectory.setText(newDir);
			
	# Set working copy directory callback wrapper
	def setTempFilesDir(self, value):
		# flush back to project settings, but only if different
		if project.tempFilesDir != str(value):
			project.setTempFilesDir(str(value));
		else:
			print "td paths same"
		
	# Skip-List -------------------------------------------
	
	# make sure that there is a valid skip path before allowing adding...
	def validateNewSkipPathLength(self):
		# get path, and strip off all whitespace
		path = str(self.wSkipListNewItem.text()).strip();
		
		# only if there's content and it exists may we continue
		if path:
			fullPath = os.path.join(project.workingCopyDir, path);
		else:
			fullPath = "";
			
		ok = os.path.exists(fullPath);
		self.wSkipListAdd.setEnabled(ok);
		
		return ok;
	
	# ..................
	
	# Add item to skip list
	def skiplistAdd(self):
		# get value from new-item widget
		newVal = str(self.wSkipListNewItem.text()).strip();
		if not newVal:
			print "No item to add to skiplist"
			return;
		
		# add this to the underlying list, then to the view as well
		if newVal not in project.skiplist:
			project.addSkipPath(newVal);
			self.wSkipListView.addItem(newVal);
			
		# clear textbox, now we're done
		self.wSkipListNewItem.setText("");
		
		# send update signals
		self.emit(SIGNAL('skiplistChanged()'));
	
	# Remove selected items
	def skiplistRemove(self):
		# get list of selected items
		selItems = self.wSkipListView.selectedItems();
		if len(selItems) == 0: # TODO: this shouldn't happen... we should have selection poll
			print "No items selected"
			return;
			
		# remove these items from the lists
		for item in selItems:
			project.removeSkipPath(item.text());
			self.wSkipListView.takeItem(self.wSkipListView.row(item));
		
		# send update signals
		self.emit(SIGNAL('skiplistChanged()'));
		
	# Toggle selection of all items in list
	def skiplistToggleSel(self):
		# anything selected?
		# TODO: there has to be a faster/more efficient way!
		if len(self.wSkipListView.selectedItems()):
			self.wSkipListView.clearSelection();
		else:
			self.wSkipListView.selectAll();

#########################################
