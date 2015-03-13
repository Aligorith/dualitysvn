# System Requirements #

These are just representative system requirements that are known to work (as of 2010 December 22). Other configurations may also work, but no guarantees are made on whether these will be fully-functional.

  * [[Python 2.6](http://www.python.org)] - Python 2.5/2.7 will also probably work too. NOT compatible with Py3k though
  * [[PyQt 4.7/4.8](http://www.riverbankcomputing.co.uk/software/pyqt/intro)] - the PyQt4 series is required. Older versions of this series could be used, but suffer from crashes on exit, which are related to the "item model" widgets.
  * [[SVN 1.16](http://subversion.tigris.org/)] - older clients may still be ok, but use at your own risk (with regard to non-existent or changed arguments).

# Current Developer Setup #

These are the specific details of the main developer's setup (as of December 2010/February 2011), and should be a good guideline for what will work.

  * Windows Vista
  * Python 2.6.3 - installed to default (`C:\python26\`) and included on PATH
  * PyQt 4.7.0 - installed for Py2.6 (default locations)
  * SVN 1.16.13 - installed via installer and included on PATH

# Installation #

Generic Instructions:
  1. Install all the necessary dependencies. The recommended order for this is currently Python, then PyQt, followed by SVN (though SVN can be installed before Python instead).
  1. Unzip the latest zip-bundle from the Downloads page somewhere on your computer. It is strongly recommended to avoid placing this in a directory with spaces in its name (this advice especially applies to Windows users, who should not install under "C:\Program Files\" under any circumstances).

Platform specific:
  * On Windows...
    1. Create a shortcut to dualitysvn.bat and put this in a convenient place (i.e. desktop). You can find an icon to use for this in the icons folder.
    1. It may be convenient to associate `*.duality` files with dualitysvn.bat at some point to make it easier to load project files
  * On other platforms... (untested)
    1. Create a shell script (with executable permissions) in your favourite text editor, with a command like
```
python dualSvn.py $*
```
> > and do whatever is needed to make this easily accessible. Such a script may be included in the official bundle in a later release after having been officially tested.