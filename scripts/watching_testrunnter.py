#!/usr/bin/env python

import glob
import os
import sys
import time


class FileWatcher(object):
    def __init__(self, basepath, watch_wildcard):
        self.basepath = basepath
        self.wildcard = watch_wildcard
        self.existing_files = {}
    
    def file_did_change(self, filename):
        change_detected = False
        
        current_mtime = os.path.getmtime(filename)
        if filename in self.existing_files:
            known_mtime = self.existing_files[filename]
            if known_mtime < current_mtime:
                change_detected = True
        else:
            # TODO: Currently there is no handling of deleted files.
            change_detected = True
        self.existing_files[filename] = current_mtime
        return change_detected
    
    def _check_for_file_changes_in_dir(self, topdir):
        change_detected = False
        filenames = glob.glob(os.path.join(topdir, self.wildcard))
        for filename in filenames:
            if self.file_did_change(filename):
                change_detected = True
        return change_detected
    
    def _check_for_changes_in_subdirs(self, topdir):
        change_detected = False
        for item in os.listdir(topdir):
            itemname = os.path.join(topdir, item)
            if os.path.isdir(itemname):
                change_in_subdirectory = self.did_files_change(itemname)
                if change_in_subdirectory == True:
                    change_detected = True
        return change_detected
    
    def did_files_change(self, topdir=None):
        if topdir is None:
            topdir = self.basepath
        file_changed = self._check_for_file_changes_in_dir(topdir)
        subdir_changed = self._check_for_changes_in_subdirs(topdir)
        return (file_changed or subdir_changed)
    

class Command(object):
    def __init__(self, cmd):
        self.cmd = cmd
    
    def execute(self):
        os.system(self.cmd)


def main(argv):
    if len(argv) == 1 or len(argv) > 4:
        sys.exit('usage: %s command [basepath [watch_wildcard]]' % os.path.basename(argv[0]))
    shell_command = argv[1]
    basepath = '.'
    watch_wildcard = '*.py'
    if len(argv) > 2:
        basepath = argv[2]
    if len(argv) > 3:
        watch_wildcard = argv[3]
    command = Command(shell_command)
    watcher = FileWatcher(basepath, watch_wildcard)
    while True:
        if watcher.did_files_change():
            command.execute()
            print " -- done --"
        time.sleep(1)


if __name__ == '__main__':
    main(sys.argv)
