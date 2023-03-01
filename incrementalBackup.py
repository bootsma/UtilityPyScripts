# Incremental Backup Script
# Author: Gregory J. Bootsma
# Version: 1.0
# Copyright (C) 2022

import argparse
import copy
import os
import filecmp
import shutil
import fnmatch
import sys

from datetime import datetime, timezone
#from distutils.dir_util import copy_tree

from distutils import log
log.set_verbosity(log.INFO)
log.set_threshold(log.INFO)

version = '1.0'


def init_args():
    parser = argparse.ArgumentParser(description="incrementalBackup.py <SOURCE> <LATEST>\n"
                                                 " Version: {}\n"
                                                 " Author: Gregory J. Bootsma, Copyright 2022\n"
                                                 " Description:\n\t"
                                                 "Takes two directories SOURCE and LATEST. The source directory is the "
                                                 "data you would like to backup. The LATEST directory is the location of\n\t"
                                                 "the last backup made (e.g. ..\MYDATA_LATEST). The LATEST directory will"
                                                 " be renamed with the date it was created  (e.g. SOURCEDIRNAME-YYYY-MM-DD-HHhMMmSSs). \n\t"
                                                 "A new directory will be created that is a linked copy of the previous "
                                                 "latest. This directory will be compared to SOURCE and any changed files \n\t"
                                                 "will be replaced with a newest version.".format(version), formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('source', type=str, help="source directory")
    parser.add_argument('latest', type=str, help="directory of latest data, or desired destination if first time "
                                                 "running")
    parser.add_argument('-v', '--verbose', action = 'store_true', help='Sets verbosity on will give details of '
                                                                       'actions as run.')
    parser.add_argument('-t','--test', action='store_true', help='Turns on testing mode directories are only '
                                                                 'compared, nothing changes.')

    parser.add_argument('-s','--use_symbolic_links', action='store_true', help='If set will use symbolic links, default is to use hard links.')

    parser.add_argument('-o','--omit_list',type=str,help='List of directory/file names to exclude, can use patterns,\n'
                                                '(e.g  -o test,logs,*.exe)')
    return parser.parse_args()




def copy2_verbose(src, dst):
    print('Copying {0}'.format(src))
    shutil.copy2(src,dst)

default_use_symbolic = False

def make_link(src_path:str, lnk_path:str, use_symbolic = default_use_symbolic):
    if not use_symbolic:
        os.link(src_path,lnk_path)
    else:
        os.symlink(src_path,lnk_path)



def my_copy_tree(src, dst, verbose=False, ignore_list=None):

    if ignore_list is None:
        ignore = None
    elif  len(ignore_list) < 1:
        ignore = None
    else:
        ignore = shutil.ignore_patterns(*ignore_list)

    if verbose:
        shutil.copytree(src, dst, ignore=ignore, copy_function=copy2_verbose)
    else:
        shutil.copytree(src,dst,ignore=ignore)


class IgnoreFilesFilter:
    """
    Ignore List to be used in filecmp functions, supports wild cards through use of in_list,
    filecmp functions handle wildcards (*) on there own
    """


    def __init__(self, ignore_list:list):
        self._has_wildcards = False
        self._ignore_list = ignore_list

        if ignore_list is not None:
            for word in ignore_list:
                if '*' in word:
                    self._has_wildcards = True
                    break

    @property
    def ignore_list(self):
        return self._ignore_list

    def filter_list(self, list_to_filter:list)->list:
        return [x for x in list_to_filter if not self.in_list(x)]

    def filter_dircmp(self, dircmp: filecmp.dircmp)->filecmp.dircmp:
        """
        Filters the files from the right_only, left_only, diff_files,
        :param dircmp: filecmp.dircmp see https://docs.python.org/3/library/filecmp.html
        :return: rtn_dircmp: a modified copy of dircmp (filecmp.dircmp class)
        """
        rtn_dircmp = copy.deepcopy(dircmp)
        rtn_dircmp.left_list = self.filter_list(dircmp.left_list)
        rtn_dircmp.right_list = self.filter_list(dircmp.right_list)
        rtn_dircmp.common = self.filter_list(dircmp.common)
        rtn_dircmp.right_only = self.filter_list(dircmp.right_only)
        rtn_dircmp.left_only = self.filter_list(dircmp.left_only)
        rtn_dircmp.common_dirs = self.filter_list(dircmp.common_dirs)
        rtn_dircmp.common_files = self.filter_list(dircmp.common_files)
        rtn_dircmp.common_funny = self.filter_list(dircmp.common_funny)
        rtn_dircmp.same_files = self.filter_list(dircmp.same_files)
        rtn_dircmp.diff_files = self.filter_list(dircmp.diff_files)
        rtn_dircmp.funny_files = self.filter_list(dircmp.funny_files)
        rtn_dircmp.subdirs = self.filter_list(dircmp.subdirs)

        return rtn_dircmp


    def in_list(self, path_or_file:str):

        word = os.path.basename(path_or_file)
        if self._ignore_list is None or len(self._ignore_list) <1:
            return False

        if self._has_wildcards:
            for item in self._ignore_list:
                if fnmatch.fnmatch(word,item):
                    return True
            return False
        else:
            if word in self._ignore_list:
                return True
            else:
                return False



def create_links_of_files(src, dest, verbosity, ignore_filter:IgnoreFilesFilter):
    """
    Creates copy of the directory structure found
    :param src: Source directory
    :param dest: Destination directory
    :param verbosity: True to display information to console
    :return: None
    """

    print( 'Calling CLF: src: {}, dst: {}'.format(src,dest))
    if not os.path.exists(dest) or not ignore_filter.in_list(dest):
        os.mkdir(dest)
    else:
        print('WARNING: Directory {} already exists.'.format(dest))
    if verbosity:
        print('Created directory {}.'.format(dest))
    #for (dirpath, dirnames, filenames ) in os.walk(src):
    for item in os.listdir(src):
        curr_src_item = os.path.join(src, item)
        curr_dst_item = os.path.join(dest, item)
        if ignore_filter.in_list(item):
            pass
        elif os.path.isdir(curr_src_item):
            create_links_of_files(curr_src_item, curr_dst_item,verbosity, ignore_filter)
        else:
            make_link(curr_src_item, curr_dst_item)
            print('Linking source {} to {}'.format(curr_src_item, curr_dst_item))


def compare_replace_and_remove(src, dst, verbosity, ignore_filter:IgnoreFilesFilter=None, test = False):
    """
    :param ignore_filter:
    :param src: The source directory of data
    :param dst: The directory we will compare the src data with, if test is False different or new data is copied from src to dst
    :param verbosity: if True output about the each operation performed or difference found is displayed
    :param test: If test is True only information about compared data is displayed no changes occur
    :return:  return true if any changes found between directories
    """
    if ignore_filter is None:
        ignore_filter = IgnoreFilesFilter([])

    data_changed = False

    rtn = filecmp.dircmp( src, dst)

    local_diff=False
    if len(rtn.right_only)> 0 or len(rtn.left_only) >0 or len(rtn.diff_files) > 0:
        local_diff = True

    if len(rtn.funny_files) > 0 or len(rtn.common_funny) >0:
        raise Exception(f'There were funny files found when comparing {src} to {dst}\n'
                        f'Funny Files: {rtn.funny_files}\n'
                        f'Common Funny Files: {rtn.common_funny}'
                        )

    if verbosity:
        print('Comparing src [{}] to dst [{}] : [Local Diff] : [{}]'.format(src, dst, local_diff))

    for item in rtn.right_only:
        data_changed = True
        full_path_item = os.path.join(dst, item)
        if os.path.isdir(full_path_item):

            if verbosity:
                print('Need to remove directory and contents: {}.'.format(full_path_item))
            if not test:
                shutil.rmtree(full_path_item)
                if verbosity:
                    print('Removed directory and contents: {}.'.format(full_path_item))

        else:
            if verbosity and test:
                print('Need to remove file: {}.'.format(full_path_item))
            if not test:
                os.remove(full_path_item)
                if verbosity and test:
                    print('Removed file: {}.'.format(full_path_item))

    # new item
    for item in rtn.left_only:
        data_changed = True
        if not ignore_filter.in_list(item):
            full_path_item = os.path.join(src, item)
            dst_path_item = os.path.join(dst, item)
            if os.path.isdir(full_path_item):
                if verbosity:
                    print('Need to copy directory {} to {}.'.format(full_path_item, dst_path_item))
                if not test:
                    my_copy_tree(full_path_item, dst_path_item, verbose=verbosity, ignore_list=ignore_filter.ignore_list)
                if verbosity:
                    print('Copied directory (recursively) {} to {}'.format(full_path_item, dst_path_item))
            else:
                if verbosity and test:
                    print('Need to copy file {} to {}.'.format(full_path_item,dst_path_item))
                if not test:
                    shutil.copy2(full_path_item, dst_path_item)
                if verbosity and not test:
                    print('Copied file {} to {}.'.format(full_path_item,dst_path_item))

    for item in rtn.diff_files:
        data_changed = True
        full_path_item = os.path.join(src, item)
        dst_path_item = os.path.join(dst, item)
        if os.path.isdir(full_path_item):
            raise Exception('Found a directory in what should only be files {}.'.format(full_path_item))
        else:
            if verbosity and test:
                print('Need to replace file {} with {}.'.format(dst_path_item, full_path_item))
            if not test:

                # need to remove the old link/file first otherwise if it is a linked file
                # shutil overwrites the file linked to not just the linked file
                os.remove( dst_path_item)
                shutil.copy2(full_path_item, dst_path_item)
            if verbosity and not test:
                print('Replaced file {} with {}.'.format(dst_path_item, full_path_item))

    #check the common dirs:
    for common_dir in rtn.common_dirs:
        full_path_left =os.path.join(src, common_dir)
        full_path_right = os.path.join(dst, common_dir)
        data_changed = compare_replace_and_remove( full_path_left, full_path_right, verbosity, ignore_filter, test) or data_changed



    return data_changed


if __name__ == '__main__':

    print(sys.argv)

    args = init_args()


    if not os.path.isdir(args.source):
        print('Source location [{}] is not a directory.'.format(args.source))

    print('Using symbolic links: {}'.format(args.use_symbolic_links))
    default_use_symbolic = args.use_symbolic_links

    ignore_list = None
    if args.omit_list is not None:
        ignore_list = args.omit_list.split(',')
        if len(ignore_list) == 1:
            if len(ignore_list[0]) <1:
                ignore_list = None

    first_run = True
    if os.path.isdir( args.latest ):
        first_run = False
    else:
        if args.test:
            print('Latest directory [{}] does not exist, nothing to compare.'.format(args.latest))

    if args.test:
        args.verbose = True
        print('Running in testing mode (comparison only)')
        print('Source: {}\nLatest: {}\n '.format(args.source, args.latest))
        rtn = compare_replace_and_remove(args.source, args.latest, args.verbose, ignore_list, True)
        print('\nDifferences: {}\n'.format(rtn))
        exit(rtn)

    if first_run:
        if args.verbose:
            print('First run detected. Copying all data from {} to {}.'.format(args.source, args.latest))
        if os.path.isdir(args.latest):
            shutil.rmtree(args.latest)

        #os.mkdir(args.latest)

        my_copy_tree(args.source, args.latest, ignore_list=ignore_list, verbose=args.verbose)
        #copy_tree(args.source, args.latest, verbose = args.verbose)


    else:
        source = os.path.abspath(args.source)
        latest = os.path.abspath(args.latest)

        # Move current latest
        source_name = source.split('\\')[-1]
        storage_location = os.path.abspath('\\'.join(latest.split('\\')[:-1]))
        folder_creation_time = datetime.fromtimestamp(os.stat(args.latest).st_ctime)
        new_folder_name = os.path.join(storage_location,source_name+'_'+folder_creation_time.strftime("%Y-%m-%d-%Hh%Mm%Ss"))

        os.rename(latest, new_folder_name)

        if args.verbose:
            print('Latest Data {} moved to {}.'.format(latest, new_folder_name))

        #Create link to latest into latest for comparison
        #os.mkdir(latest)
        ignore_filter = IgnoreFilesFilter(ignore_list)
        print('Src: {}, Dst: {}'.format(new_folder_name, latest))
        create_links_of_files(new_folder_name, latest, args.verbose, ignore_filter)
        if args.verbose:
            print('Linked Data from {}  to {}.'.format(new_folder_name, latest))

        change = compare_replace_and_remove(source, latest, args.verbose, ignore_filter)
        if not change:
            print('[ Directories are identical. ]')



