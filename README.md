# UtilityPyScripts

A collection of python scripts for random things..

# incrementalBackup.py

Incremental backup script that can be run on Windows/Linux as a task to create backups 
of a folder at specific points and time. It can us hard links or symbolic links (hard links recommended). Allows
you to view what a folder looked like at a specific point in time without the cost of space (only file changes 
create new data).


**Usage:**

<ul>
  ## incrementalBackup.py <SOURCE> <LATEST>                                                                                                                              
  <ul>
   Version: 1.0                                                                                                                                                       
   Author: Gregory J. Bootsma, Copyright 2022     

      
   <ul>
   Description:                                                                                                                                                       
    <ul>
          Takes two directories SOURCE and LATEST. The source directory is the data you would like to backup. The LATEST directory is the location of                 
          the last backup made (e.g. ..\MYDATA_LATEST). The LATEST directory will be renamed with the date it was created  (e.g. SOURCEDIRNAME-YYYY-MM-DD-HHhMMmSSs). 
          A new directory will be created that is a linked copy of the previous latest. This directory will be compared to SOURCE and any changed files               
          will be replaced with a newest version.                                                                                                                     
    </ul>
   </ul>
    
  <ul>
  positional arguments:           
    <ul>
    source &emsp; source directory                                                                                                                            
    latest &emsp; directory of latest data, or desired destination if first time running
    </ul>
  </ul>
    
  <ul>
  optional arguments:
  <ul>
    -h, --help     &emsp;   &emsp;    show this help message and exit
    -v, --verbose  &emsp;   &emsp;    Sets verbosity on will give details of actions as run.
    -t, --test     &emsp;  &emsp;     Turns on testing mode directories are only compared, nothing changes.
    -s, --use_symbolic_links&emsp;     If set will use symbolic links, default is to use hard links.
    -o OMIT_LIST, --omit_list OMIT_LIST &emsp;
                          List of directory/file names to exclude, can use patterns,
                          (e.g  -o test,logs,*.exe)
    </ul>
   </ul>
  </ul>
