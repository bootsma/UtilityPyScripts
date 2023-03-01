# Purge Duplicate Backup Scripts
# Author: Gregory J. Bootsma
# Version: 1.0
# Copyright (C) 2022

import argparse
import os
import filecmp
import shutil

version='1.0'

from distutils import log
log.set_verbosity(log.INFO)
log.set_threshold(log.INFO)


from incrementalBackup import compare_replace_and_remove

def compare_directories(src:str, dst:str, verbose:bool=False, shallow:bool=True):
    """
    Does a comparison of two directories and all subdirectories looking for a difference.
    If a difference is found False is returned.
    
    :param src:
    :param dst:
    :param verbose: outputs info if true
    :param shallow: same as filecmp.cmp definition of shallow
    :return: True if same, False if different
    """

    rtn = filecmp.dircmp(src, dst)

    if rtn.funny_files or rtn.common_funny:
        raise Exception(f'There were funny files found when comparing {src} to {dst}\n'
                        f'Funny Files: {rtn.funny_files}\n'
                        f'Common Funny Files: {rtn.common_funny}'
                        )

    if rtn.right_only or rtn.left_only or rtn.diff_files:
        if verbose:
            print(f'Difference in {src} when compared to {dst}')
            if rtn.right_only:
                print(f'The following where only found in right side [{src}]:\n {rtn.right_only}')
            if rtn.left_only:
                print(f'The following where only found in left side [{dst}]:\n {rtn.left_only}')
            if rtn.diff_files:
                print(f'The following different files were found in {dst}:\n {rtn.diff_files}')

        return False
    else:
        if not shallow:
            _,mismatch,errors=filecmp.cmpfiles(src, dst, rtn.common_files, shallo=False)
            if mismatch:
                if verbose:
                    print(f'The following files did not match when comparing {src} to {dst}:\n {mismatch}')
                return False
            if errors:
                raise Exception(f'The following files found when comparing {src} and {dst} caused errors and could not be compared.'
                                f'Files: {errors}')

    for common_dir in rtn.common_dirs:
        if not compare_directories(os.path.join(src, common_dir), os.path.join(dst, common_dir), verbose, shallow):
            return False

    return True




def init_args():

    parser = argparse.ArgumentParser(description="purgeDuplicateBackups.py \n"
                                                 " Version: {}\n"
                                                 " Author: Gregory J. Bootsma, Copyright 2023\n"
                                                 " Description:\n\t"
                                                 " Takes the root directory where you backups created using \n\t" 
                                                 "incrementalBackup.py are stored and purges directories containing\n\t"
                                                 "identical data. This should only be used when hardlinks were used.\n\t"
                                                 "If symbolic links were used it will make a mess."
                                                 "".format(version), formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('root', type=str, help="root backup directory")
    parser.add_argument('-v', '--verbose', action = 'store_true', help='Sets verbosity on which will give details of '
                                                                       'actions as run.')
    parser.add_argument('-n', '--no_prompt', action = 'store_true', help='Well destroy directories without prompting user input')
    parser.add_argument('-d','--destroy', action='store_true', help='Turns of testing mode directories, directories will '
                                                                    'be prompted for deletion (unless --no_prompt set)')
    parser.add_argument('-s','--shallow', action='store_true', help='Uses os.stat() signatures (file type, size, '
                                                                    'and modification time) to determine if files are equal')
    return parser.parse_args()


line_break = '[==============================================================================]'

def search_and_destroy( root_dir:str, verbose:bool=False, destroy:bool=False, prompt_before_destroy:bool=True, shallow:bool=True):

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
    dirs = [os.path.join(root, d) for d in os.listdir(root) if os.path.isdir(os.path.join(root,d))]
    dirs_sorted = sorted(dirs, key=lambda d: os.path.getctime(d))


    if verbose:
        print(f'Keeping the newest directory {dirs_sorted.pop()}')

    if verbose:
        print(f'Going to compare directories starting with oldest: {dirs_sorted}')


    dirs_to_destroy = []
    curr_dir_index = 0
    while curr_dir_index < len(dirs_sorted)-1:
        curr_dir = dirs_sorted[curr_dir_index]
        directories_match = True
        for next_dir_index in range(curr_dir_index+1, len(dirs_sorted)):
            if verbose:
                print(line_break)
                print(f'Comparing {curr_dir} to {dirs_sorted[next_dir_index]}')

            #directories_match_a = not compare_replace_and_remove(curr_dir, dirs_sorted[next_dir_index], True, test=True)
            directories_match = compare_directories(curr_dir, dirs_sorted[next_dir_index], verbose=True)

            #if directories_match_a != directories_match:
            #    print("(((((((((((((ERROR))))))))))))")


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
                shutil.rmtree(dir)

if __name__ == "__main__":

    args = init_args()
    destroy =  args.destroy
    prompt_before_death = not args.no_prompt
    search_and_destroy(args.root, args.verbose, destroy, prompt_before_death, args.shallow )
