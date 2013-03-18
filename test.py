# -*- coding: utf-8 -*-
"""Test against the ZODB on python version 2.7 and 3.2"""
import os
import sys
import argparse
import transaction
from persistent import Persistent
from persistent.mapping import PersistentMapping
from BTrees.OOBTree import OOBTree
from ZODB import DB

class Folder(PersistentMapping):
    """A folder implementation..."""

    def __init__(self, name, path):
        super(Folder, self).__init__()
        self.name = name
        self.path = path


class File(Persistent):
    """A simple file entry"""

    def __init__(self, name, path):
        super(File, self).__init__()
        self.name = name
        self.path = path


def traverse(context, path=[]):
    for i in path:
        context = context[i]
    return context

def init_db(context, args):
    """Walk over the filesystem to place file entries in the database."""
    for path, dirs, files in os.walk('.'):
        split_path = path.split(os.sep)
        if split_path[0] == '.':
            split_path.pop(0)
        subcontext = traverse(context, split_path)
        for file in files:
            subcontext[file] = File(file, os.path.join(path, file))
        for dir in dirs:
            subcontext[dir] = Folder(dir, os.path.join(path, dir))
    transaction.commit()

def list_db(context, args):
    """List a folder's contents"""
    for name in context:
        print(name)

def main(argv=None):
    parser = argparse.ArgumentParser(description='ZODB bridge test script')
    v_major, v_minor = sys.version_info.major, sys.version_info.minor
    parser.add_argument('-d', '--db-file',
                        default='data-py{}.{}.fs'.format(v_major, v_minor),
                        help="Path to the database file")
    subparsers = parser.add_subparsers()
    init_parser = subparsers.add_parser('init')
    init_parser.set_defaults(func=init_db)
    list_parser = subparsers.add_parser('list')
    list_parser.set_defaults(func=list_db)

    args = parser.parse_args(argv)

    db = DB(args.db_file)
    db_conn = db.open()
    db_root = db_conn.root()
    if 'test' not in db_root:
        root = db_root['test'] = OOBTree()
    else:
        root = db_root['test']

    args.func(root, args)
    db_conn.close()

if __name__ == '__main__':
    main()
