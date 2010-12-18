# Duality SVN
# Original Author: Joshua Leung
#
# Svn Status List

from coreDefines import *

from DiffViewer import *

#########################################
# List Item Datatypes

# Data item that occurs in SvnStatusList's model
class SvnStatusListItem:
	# Class Defines ======================================
	# File Status
	FileStatusMap = {
		' ':"Unchanged",
		'A':"Added",
		'C':"Conflicted",
		'D':"Deleted",
		'I':"Ignored",
		'M':"Modified",
		'R':"Replaced",
		'X':"External",
		'?':"Unversioned",
		'!':"Missing",
		'~':"Obstructed" #versioned item obstructed by some item of a different kind
	}
	
	# Property Status
	PropStatusMap = {
		' ':"Unchanged",
		'C':"Conflicted",
		'M':"Modified"
	}
	
	# Setup ==============================================
	
	# ctor
	# < (initStr): (str) optional string to parse to get relevant info
	def __init__(self, initStr=None):
		# init placeholders
		self.defaultEnabled = True;
		
		self.path = "";
		
		self.file_status = SvnStatusListItem.FileStatusMap[' '];
		self.prop_status = SvnStatusListItem.PropStatusMap[' '];
		
		# initialise from string
		if initStr:
			self.fromString(initStr);
			
	# parse settings from a string
	# < initStr: (str) input string
	def fromString(self, initStr):
		try:
			# chop into 2 parts: status and path
			statusStr = initStr[:7]; 		 # first 7 columns 
			self.path = initStr[8:].strip(); # rest of string after status columns
			
			# decipher status string
				# col 1: file status
			self.file_status = SvnStatusListItem.FileStatusMap[statusStr[0]];
				# col 2: property status
			self.prop_status = SvnStatusListItem.PropStatusMap[statusStr[1]];
			
			# modify enabled status from placeholder
			self.setAutoDefaultEnabledStatus();
		except:
			pass;
	
	# Enabled Status ===========================================
	
	# automatically determine whether "default enabled" status is on
	def setAutoDefaultEnabledStatus(self):
		# disable based on file status, so check on each of the bad ones...
		badKeys = (' ', 'C', 'I', 'X', '?', '!');
		
		for k in badKeys:	
			if self.file_status == SvnStatusListItem.FileStatusMap[k]:
				self.defaultEnabled = False;
				break;
		else:
			# by default (i.e. if nothing caught), this is on
			self.defaultEnabled = True;

#########################################
# Reusable List Datatype

# A list of SvnStatusListItem's - subclass of list
class SvnStatusListDatalist(list):
	# Class Defines =========================================
	# Name of file to output own data to
	TARGETS_FILENAME = "duality_targets.oplist"; # FIXME: move out of this function
	
	# List Ops ==============================================
	
	# make a copy of self
	def copy(self):
		nList = SvnStatusListDatalist();
		nList[:] = self[:];
		
		return nList;
	
	# populate from given list
	# ! makes a copy of the new list's contents
	def replaceAll(self, newList):
		self[:] = newList[:];
	
	# clear list
	def clearAll(self):
		self[:] = [];
	
	# Special Ops ============================================
	
	# Data List ----------------------------------------------
	
	# filter the items in the list, using the given predicate function
	# < cb: (fn(SvnStatusListItem)=bool) predicate function to apply
	# > return[0]: (SvnStatusListDatalist) a new list with the unwanted items filtered out 
	def getFiltered(self, cb):
		nList = SvnStatusListDatalist();
		
		for item in self:
			if cb(item):
				nList.append(item);
		
		return nList;
	
	# Outputting to File --------------------------------------
	
	# get filename
	# < (opName): (str) optional name of the SVN operation which 
	def getPathsFileName(self, opName=None):
		# FIXME: the directory where this gets dumped should be user defined
		dirN = os.getcwd();
		
		# include the operation name if provided, to avoid clashes on chained ops
		if opName:
			fileN = os.path.join(dirN, opName + '_' + SvnStatusListDatalist.TARGETS_FILENAME);
		else:
			fileN = os.path.join(dirN, SvnStatusListDatalist.TARGETS_FILENAME);
			
		return fileN;
	
	# save our items' paths to a file to pass to an svn operation
	# < (opName): (str) optional name of the SVN operation which 
	# > return[0]: (str) name of file where these paths were saved to
	def savePathsFile(self, opName=None):
		# determine filename
		fileN = self.getPathsFileName(opName);
		
		# write (full) paths only to file
		with open(fileN, 'w') as f:
			for item in self:
				f.write(item.path + '\n');
		
		# return the full filename
		return fileN;

#########################################
# Data Model (Tailored for UI)

# Qt wrapper for SvnStatusListItem, which represents one "row" in the list
# TODO: implement support for hiding some items temporarily...
class SvnStatusListItemModel(QAbstractItemModel):
	# Class Defines =========================================
	# Header labels
	HeaderLabels = ("Path", "Status", "Prop Status");
	
	# Setup =================================================
	
	# ctor
	# < (listItems): (SvnStatusListDatalist) list of SvnStatusListItem's for populating as a filtered copy of another instance.
	#	! Checkboxes will not be available when such a list is supplied, as further editing isn't needed.
	def __init__(self, listItems=None, parent=None):
		super(SvnStatusListItemModel, self).__init__(parent);
		
		# store reference to the list of data being shown
		if listItems:
			self.listItems = listItems;
		else:
			self.listItems = SvnStatusListDatalist();
		self.checked = SvnStatusListDatalist();
		
		# checkboxes will only be shown if we're not being supplied with
		# a list to simply display again (in another place)
		self.checksOn = (listItems is None);
	
	# Methods ===============================================
	
	# add entry
	def add(self, item):
		# warn everybody to update
		idx = len(self.listItems); # always as last index of list
		self.beginInsertRows(QModelIndex(), idx, idx);
		
		# add to list
		self.listItems.append(item);
		
		# if "defaultEnabled", add to checked list
		if item.defaultEnabled:
			self.checked.append(item);
		
		# done updating
		self.endInsertRows();
		
	# clear all entries
	def clearAll(self):
		# just do a remove of all
		totLen = len(self.listItems);
		self.beginRemoveRows(QModelIndex(), 0, totLen);
		
		# clear lists
		self.listItems.clearAll();
		self.checked.clearAll();
		
		# done
		self.endRemoveRows();
		
	# get the item associated with the given index
	# < index: (QModelIndex) cell id wrapper
	# > return[0]: (SvnStatusListItem) item at this index (corresponding to row only)
	def getItem(self, index):
		if index.isValid():
			return self.listItems[index.row()];
		else:
			return None;
		
	# toggle select/deselect all
	def toggleAllChecked(self):
		self.beginResetModel();
		
		if len(self.checked):
			# deselect all
			self.checked.clearAll();
		else:
			# select all
			self.checked.replaceAll(self.listItems);
			
		self.endResetModel();
	
	# QAbstractItemMode implementation ======================
	
	# return the relevant data for each column's header cell
	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			# section = header name
			return QVariant(SvnStatusListItemModel.HeaderLabels[section]);
		
		return None;
		
	# total number of attributes - static
	def columnCount(self, parent):
		# columns represent different attributes per record
		return len(SvnStatusListItemModel.HeaderLabels);
		
	# total number of records - dynamic
	def rowCount(self, parent):
		# each row represents 1 record
		return len(self.listItems);
	
	# return parent index of item - nothing has parents here!
	def parent(self, index):
		# no item is a child of anything
		return QModelIndex();
		
	# get QModelIndex for row/column combination?
	# < row: (int) row number - 0 indexed
	# < col: (int) column number - 0 indexed
	# < (parent): (QModelIndex) unused...
	def index(self, row, col, parent):
		# must be within bounds
		if not self.hasIndex(row, col, parent):
			return QModelIndex();
			
		# create model-index wrapper for this cell
		return self.createIndex(row, col, self.listItems[row]); # last arg err...
	
	# get QtCore.Qt.ItemFlags
	def flags(self, index):
		if not index.isValid():
			return Qt.NoItemFlags
		
		# at very least, items can be selected
		flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable;
		
		# if we can show checkboxes, include that too
		if self.checksOn:
			flags |= Qt.ItemIsUserCheckable;
		
		return flags;
	
	# get data for model cell
	# < index: (QModelIndex) row/column reference for cell to get data for
	# < role: (QtCore.Qt.ItemDataRole/int) which aspect of cell to get data for
	# > return[0]: (QVariant) relevant data, wrapped in "QVariant" wrapper (i.e. "anything goes container")
	def data(self, index, role):
		# valid indices only
		if not index.isValid():
			return None;
		
		# get item
		item = self.getItem(index);
		
		# what data to return
		if role == Qt.DisplayRole:
			# display data - depends on the index
			if index.column() == 2:
				# property status
				return QVariant(item.prop_status);
			elif index.column() == 1:
				# status
				return QVariant(item.file_status);
			else:
				# path
				return QVariant(item.path);
		elif role == Qt.ForegroundRole:
			# text color
			if index.column() == 1:
				# status of file = color
				colorMap = {
					' ':QColor(Qt.lightGray),
					'A':QColor(Qt.darkCyan),
					'C':QColor(Qt.red),
					'D':QColor(Qt.darkMagenta),
					'I':QColor(Qt.darkYellow),
					'M':QColor(Qt.blue),
					'R':QColor(Qt.darkCyan),
					'X':QColor(Qt.yellow),
					'?':QColor(Qt.gray),
					'!':QColor(Qt.darkRed),
					'~':QColor(Qt.darkRed) #versioned item obstructed by some item of a different kind
				}
				
				# find the right one that matches for this item
				# FIXME: a bimap would solve this easily...
				for shortKey,longKey in SvnStatusListItem.FileStatusMap.iteritems():
					if longKey == item.file_status:
						return colorMap[shortKey];
				else:
					# no appropriate decoration found
					return None;
			else:
				return None;
		elif role == Qt.ToolTipRole:
			# construct tooltip for all entries
			tooltipTemplate = "\n".join([
				"<b>Path:</b> %s",
				"<b>File Status:</b> %s",
				"<b>Property Status:</b> %s"]);
			
			return QVariant(tooltipTemplate % (item.path, item.file_status, item.prop_status));
		elif (role == Qt.CheckStateRole) and (self.checksOn):
			# checkable - for first column only
			if index.column() == 0:
				return Qt.Checked if item in self.checked else Qt.Unchecked;
			else:
				return None;
		else:
			# other roles not supported...
			return None;
	
	# set data for model cell
	# < index: (QModelIndex) cell reference
	# < value: (QVariant) wrapper for data stored
	# < role: (QtCore.Qt.ItemDataRole/int) should usually be edit only...
	def setData(self, index, value, role = Qt.EditRole):
		if index.isValid():
			# get item
			item = self.listItems[index.row()];
			
			# only checkboxes are editable...
			if (index.column() == 0) and (role == Qt.CheckStateRole) and (self.checksOn):
				if (value == Qt.Checked):
					self.checked.append(item);
					return True;
				else:
					self.checked.remove(item);
					return True;
		
		# nothing done
		return False;
	
	# sort the data 
	# < col: (int) column to sort by
	# < order: (QtCore.Qt.SortOrder/int) order to sort entries in
	def sort(self, col, order = Qt.AscendingOrder):
		# column index defines the key function used
		keyFuncs = (
			lambda x: x.path,
			lambda x: x.file_status,
			lambda x: x.prop_status
		);
		
		# perform a reverse-order sort?
		rev = (order == Qt.DescendingOrder);
		
		# sort the internal list
		self.listItems.sort(key=keyFuncs[col], reverse=rev); 

#########################################
# UI Widget

# Show "status" of files/directories within working copy,
# allowing some to be included/excluded from SVN operations
class SvnStatusList(QTreeView):
	# Setup =============================================
	
	# ctor
	# < fileList: (SvnStatusListDatalist) list of items to populate model with
	def __init__(self, fileList=None):
		super(SvnStatusList, self).__init__();
		
		# view setup settings
		self.setRootIsDecorated(False);
		self.setAlternatingRowColors(True);
		self.setUniformRowHeights(True);
		
		# double-click remapping
		# - first line disables default "expand" behaviour, which causes crashes
		# - second line hooks up event catcher to implement new dbl-click behaviour 
		self.setExpandsOnDoubleClick(False);
		self.connect(self, SIGNAL("doubleClicked(QModelIndex)"), self.dblClickHandler);
		
		# allow sorting - by the file status by default
		self.setSortingEnabled(True);
		self.sortByColumn(1, Qt.AscendingOrder);
		
		# create model
		self.model = SvnStatusListItemModel(fileList);
		self.setModel(self.model);
		
		# tweak column extents
		self.setupColumnSizes();
	
	# setup column sizes
	def setupColumnSizes(self):
		# get relevant info
		head = self.header();
		dColW = head.defaultSectionSize();
		
		# disable stretching of last section - only first should stretch!
		# TODO: make that the case when resizing happens!
		head.setStretchLastSection(False);
		
		# rest of columns should be same width - 0.75 of normal only
		hColW = dColW * 0.75;
		head.resizeSection(1, hColW);
		head.resizeSection(2, hColW);
		
		# make first column large by default
		head.resizeSection(0, dColW * 1.75);
	
	# Callbacks/Overrides =====================================
	
	# override resize event to make first column stretchy
	def resizeEvent(self, event):
		head = self.header();
		
		# make first column stretchy, so that it will be calculated
		head.setResizeMode(0, QHeaderView.Stretch); # <-- make it fill space
		
		# do normal resize
		super(SvnStatusList, self).resizeEvent(event);
		
		# now restore normal mode so that users can still edit
		head.setResizeMode(0, QHeaderView.Interactive); # <-- make it editable again
	
	# double-click event handler -> get diff for file
	# < index: (QModelIndex) the index of the item double-clicked on
	def dblClickHandler(self, index):
		# grab the item involved, then launch diff-viewer...
		item = self.model.getItem(index);
		if item:
			# run svn diff operation
			# TODO: it might be better for performance to use QProcess to gradually update stuff...
			args = ["svn", "diff", "--non-interactive", str(item.path)];
			p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=project.workingCopyDir);
			
			# show the log in some viewer dialog
			diffView = DiffViewer(self);
			diffView.displayDiff_fromString(p.stdout.read());
			diffView.show();
	
	# Methods ===========================================
	
	# Get list of selected items to operate on
	def getOperationList(self):
		# just return a copy of the model's list...
		if self.model.checksOn:
			return self.model.checked.copy();
		else:
			return self.model.listItems.copy();

#########################################
