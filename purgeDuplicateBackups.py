# Purge Duplicate Backup Scripts
# Author: Gregory J. Bootsma
# Version: 1.0
# Copyright (C) 2022

import argparse
import os
import filecmp
import shutil
import stat

version = '1.0'

from distutils import log

log.set_verbosity(log.INFO)
log.set_threshold(log.INFO)

from incrementalBackup import compare_replace_and_remove
from incrementalBackup import IgnoreFilesFilter


def compare_directories(src: str, dst: str, verbose: bool = False, shallow: bool = True, ignore_files: IgnoreFilesFilter = None):
    """
    Does a comparison of two directories and all subdirectories looking for a difference.
    If a difference is found False is returned.
    
    :param src: left side compares to right
    :param dst: right side compares to left
    :param verbose: outputs info if true
    :param shallow: same as filecmp.cmp definition of shallow
    :param ignore_files: list of files to ignore (can use wild card)
    :return: True if same, False if different
    """


    dir_comparison = filecmp.dircmp(src, dst)

    if dir_comparison.funny_files or dir_comparison.common_funny:
        raise Exception(f'There were funny files found when comparing {src} to {dst}\n'
                        f'Funny Files: {dir_comparison.funny_files}\n'
                        f'Common Funny Files: {dir_comparison.common_funny}'
                        )
    if ignore_files:
        dir_comparison = ignore_files.filter_dircmp(dir_comparison)

    if dir_comparison.right_only or dir_comparison.left_only or dir_comparison.diff_files:

        if verbose:
            print(f'Difference in {src} when compared to {dst}')
            if dir_comparison.right_only:
                print(f'The following where only found in right side [{src}]:\n {dir_comparison.right_only}')
            if dir_comparison.left_only:
                print(f'The following where only found in left side [{dst}]:\n {dir_comparison.left_only}')
            if dir_comparison.diff_files:
                print(f'The following different files were found in {dst}:\n {dir_comparison.diff_files}')

        return False
    else:
        if not shallow:
            _, mismatch, errors = filecmp.cmpfiles(src, dst, dir_comparison.common_files, shallow=shallow)
            if mismatch:
                if verbose:
                    print(f'The following files did not match when comparing {src} to {dst}:\n {mismatch}')
                return False
            if errors:
                raise Exception(
                    f'The following files found when comparing {src} and {dst} caused errors and could not be compared.'
                    f'Files: {errors}')

    for common_dir in dir_comparison.common_dirs:
        if not compare_directories(os.path.join(src, common_dir), os.path.join(dst, common_dir), verbose, shallow):
            return False

    return True


def init_args():
    parser = argparse.ArgumentParser(description="purgeDuplicateBackups.py \n"
                                                 " Version: {}\n"
                                                 " Author: Gregory J. Bootsma, Copyright 2023\n"
                                                 " Description:\n\t"
                                                 " Takes the root directory wpythere you backups created using "
                                                 "incrementalBackup.py are stored and checks for directories "
                                                 "containing identical data. If --destroy is set the data "
                                                 "will be deleted if user agrees.\n\t"
                                                 "WARNING: This should only be used when hardlinks were used. "
                                                 "If symbolic links were used it will make a mess."
                                                 "".format(version), formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('root', type=str, help="root backup directory")
    parser.add_argument('-v', '--verbose', action='store_true', help='Sets verbosity on which will give details of '
                                                                     'actions as run.')
    parser.add_argument('-n', '--no_prompt', action='store_true',
                        help='Destroy directories without prompting user input!')
    parser.add_argument('-d', '--destroy', action='store_true',
                        help='Turns of testing mode directories, directories will '
                             'be prompted for deletion (unless --no_prompt set)')
    parser.add_argument('-s', '--shallow', action='store_true', help='Uses os.stat() signatures (file type, size, '
                                                                     'and modification time) to determine if files '
                                                                     'are equal')
    parser.add_argument('-i','--ignore_list',type=str,help='List of directory/file names to exclude, can use patterns,'
                                                           'seperated by comma (e.g  -i test,logs,*.exe)')

    return parser.parse_args()


line_break = '[==============================================================================]'

def remove_readonly(func, path, _):
    "Clear readonly bit when deleting files to avoid WinError 5 that occurs when deleting files that are readonly"
    os.chmod(path, stat.S_IWRITE)
    func(path)

def search_and_destroy(root_dir: str, verbose: bool = False, destroy: bool = False, prompt_before_destroy: bool = True,
                       shallow: bool = True,  ignore_files: IgnoreFilesFilter = None):
    if not os.path.isdir(root_dir):
        print(f"There was no directory {root_dir}")
        return
    if not destroy:
        print('Running purge of duplicate backups in testing mode (e.g. no directories will be deleted)')
    else:
        if not prompt_before_destroy:
            print('Running purge of duplicate backups, no_prompt (-p) set data will be destroyed automatically.')
        else:
            print('Running purge of duplicate backups will prompt before deleting data.')

    root = os.path.abspath(root_dir)
    dirs = [os.path.join(root, d) for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
    dirs_sorted = sorted(dirs, key=lambda d: os.path.getctime(d))

    keep_oldest = dirs_sorted.pop()
    if verbose:
        print(f'Keeping the newest directory {keep_oldest}')

    if verbose:
        print(f'Going to compare directories starting with oldest: {dirs_sorted}')

    dirs_to_destroy = []
    curr_dir_index = 0
    while curr_dir_index < len(dirs_sorted) - 1:
        curr_dir = dirs_sorted[curr_dir_index]
        directories_match = True
        for next_dir_index in range(curr_dir_index + 1, len(dirs_sorted)):
            if verbose:
                print(line_break)
                print(f'Comparing {curr_dir} to {dirs_sorted[next_dir_index]}')

            # todo use this if you want info on all the differences
            # directories_match_a = not compare_replace_and_remove(curr_dir, dirs_sorted[next_dir_index], True, test=True)

            directories_match = compare_directories(curr_dir, dirs_sorted[next_dir_index], verbose=True,
                                                    shallow=shallow, ignore_files=ignore_files)


            if verbose:
                print(f'Directories match: {directories_match}')
                print(line_break)
            if not directories_match:
                break
            else:
                dirs_to_destroy.append(dirs_sorted[next_dir_index])

        curr_dir_index = next_dir_index

    if dirs_to_destroy:
        print(f'\nThe directories which are the same and can be be removed are:\n')
        print('\n'.join(dirs_to_destroy))
    else:
        print('No duplicate directories found.')
        return

    if destroy:
        proceed_to_destroy = False
        if prompt_before_destroy:
            user_input = input('Proceed with deletion of directories? (yes or no)\n')
            if user_input == 'yes':
                proceed_to_destroy = True
        else:
            proceed_to_destroy = True

        if proceed_to_destroy:
            for dir in dirs_to_destroy:
                print(f'Deleting {dir}')
                shutil.rmtree(dir, onerror=remove_readonly )


if __name__ == "__main__":

    args = init_args()
    destroy = args.destroy
    prompt_before_death = not args.no_prompt

    ignore_list = None
    if args.ignore_list is not None:
        ignore_list = args.ignore_list.split(',')
        if len(ignore_list) == 1:
            if len(ignore_list[0]) <1:
                ignore_list = None

    ignore_filter = IgnoreFilesFilter(ignore_list)

    search_and_destroy(args.root, args.verbose, destroy, prompt_before_death, args.shallow, ignore_filter)
