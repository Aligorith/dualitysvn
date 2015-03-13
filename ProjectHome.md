## What ##
A little GUI utility to create and manage a new SVN branch that gets updated easily by having the working copy simultaneously being tagged with the metadata for two branches in the same SVN tree.

This was born out of frustration with the sluggishness and largely unnecessary fuss associated with standard SVN merging which made branches largely unusable in SVN.

It also doubles as a streamlined GUI for day to day work with SVN, focused on getting common tasks done.

## When ##
This utility is designed for the case where you have a situation where you've got 2 "branches" where development is taking place: a "trunk" and a "development branch".

Assuming you've already got a working copy of "trunk" set up, ready to be branched, this utility can then be used to set up a branch in the repository and at the same time set up your working copy to be able to:
1) commit to either the branch or the trunk
2) recieve updates made in either the branch or the trunk with no more effort than a "standard update" would entail

## Current Status ##
See [CurrentStatus](CurrentStatus.md)

## Tech Notes ##
This project is 100% proudly non-PEP8 compliant Python 2.x code (not considering any external libraries which may be doing whatever they want).