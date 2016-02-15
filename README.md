dualitysvn
==========
Simpler SVN Branch Management


#What

A little GUI utility to create and manage a new SVN branch that gets updated easily by having the working copy simultaneously being tagged with the metadata for two branches in the same SVN tree.

This was born out of frustration with the sluggishness and largely unnecessary fuss associated with standard SVN merging which made branches largely unusable in SVN.

It also doubles as a streamlined GUI for day to day work with SVN, focused on getting common tasks done.


# When

This utility is designed for the case where you have a situation where you've got 2 "branches" where development is taking place: a "trunk" and a "development branch".

Assuming you've already got a working copy of "trunk" set up, ready to be branched, this utility can then be used to set up a branch in the repository and at the same time set up your working copy to be able to: 1) commit to either the branch or the trunk 2) recieve updates made in either the branch or the trunk with no more effort than a "standard update" would entail


# System Requirements

These are just representative system requirements that are known to work (as of 2010 December 22). Other configurations may also work, but no guarantees are made on whether these will be fully-functional.

 *  [Python 2.6] - Python 2.5/2.7 will also probably work too. NOT compatible with Py3k though
 *  [PyQt 4.7/4.8] - the PyQt4 series is required. Older versions of this series could be used, but suffer from crashes on exit, which are related to the "item model" widgets.
 *  [SVN 1.16] - older clients may still be ok, but use at your own risk (with regard to non-existent or changed arguments).

### Current Developer Setup

These are the specific details of the main developer's setup (as of December 2010/February 2011), and should be a good guideline for what will work.

 *  Windows Vista
 *  Python 2.6.3 - installed to default (C:\python26\) and included on PATH
 *  PyQt 4.7.0 - installed for Py2.6 (default locations)
 *  SVN 1.16.13 - installed via installer and included on PATH

# Installation

### Generic Instructions: 
 1. Install all the necessary dependencies. 
 
    The recommended order for this is currently Python, then PyQt, 
    followed by SVN (though SVN can be installed before Python instead). 
    
 2. Unzip the latest zip-bundle from the Downloads page somewhere on your computer. 
 
    It is strongly recommended to avoid placing this in a directory with spaces in its name 
    (this advice especially applies to Windows users, who should not install under "C:\Program Files\" under any circumstances).

### Platform specific: 
 * On Windows... 
   1. Create a shortcut to dualitysvn.bat and put this in a convenient place (i.e. desktop). 
      You can find an icon to use for this in the icons folder. 
      
   2. It may be convenient to associate *.duality files with dualitysvn.bat at some point to make 
      it easier to load project files 
      
 * On other platforms... (untested) 
   1. Create a shell script (with executable permissions) in your favourite text editor, 
      with a command like 
```
      python dualSvn.py $*
```

    and do whatever is needed to make this easily accessible. Such a script may be included in the official 
    bundle in a later release after having been officially tested.




# Tech Notes

This project is 100% proudly non-PEP8 compliant Python 2.x code (not considering any external libraries which may be doing whatever they want).


# Version History

* **2011 Feb 20**

The first official release, given the unassuming version number of "0.1" has now been officially released.

* **2010 Dec 08**

After over a week of heavy development, this project has finally reached an important milestone: "self-hosting". In the context of this tool, this means that it is now possible to carry out the most basic of development tasks, although support for some tools is still lacking.

However, this is still not recommended for general public usage yet. Adventurous testers are of course welcome, though support requests will most likely be ignored at this stage.

* **2010 Nov 30**

Development of this project has now been moved online.

However, this is still heavily in development, and is not intended for public use yet (if at all possible).

