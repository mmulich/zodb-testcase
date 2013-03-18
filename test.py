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


class Root(OOBTree):
    """Root class only to be used at the root of the DB
    The path on the root object is the filesystem path location.

    """

    def __init__(self, name, path):
        super(Root, self).__init__()
        self.name = name
        self.path = path


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
        filepath = os.path.join(path, name)
        with open(filepath, 'r') as file:
            self.content = file.read()

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
            subcontext[file] = File(file, path)
        for dir in dirs:
            subcontext[dir] = Folder(dir, path)
    transaction.commit()

def list_db(context, args):
    """List a folder's contents"""
    for name in context:
        print(name)

def compare_db(context, args):
    """Compare the contents"""
    bad_compares = []
    for obj in context.values():
        if not isinstance(obj, File):
            continue
        filepath = os.path.join(obj.path, obj.name)
        with open(filepath, 'r') as file:
            file_content = file.read()
            if file_content == obj.content:
                bad_compares.append(filepath)
    print('Bad comparisons:')
    print('\n'.join(bad_compares))

def main(argv=None):
    parser = argparse.ArgumentParser(description='ZODB bridge test script')
    v_major, v_minor = sys.version_info.major, sys.version_info.minor
    default_db = os.path.join('.', 'data-py{}.{}.fs'.format(v_major, v_minor))
    parser.add_argument('-d', '--db-file', default=default_db,
                        help="Path to the database file")
    subparsers = parser.add_subparsers()
    init_parser = subparsers.add_parser('init')
    init_parser.set_defaults(func=init_db)
    list_parser = subparsers.add_parser('list')
    list_parser.set_defaults(func=list_db)
    compare_parser = subparsers.add_parser('compare')
    compare_parser.set_defaults(func=compare_db)

    args = parser.parse_args(argv)

    db = DB(args.db_file)
    db_conn = db.open()
    db_root = db_conn.root()
    if 'test' not in db_root:
        root_path = args.db_file.split(os.sep)[:-1]
        if root_path:
            root_path = os.path.join(*root_path)
            root_path = os.path.abspath(root_path)
        else:
            root_path = os.path.abspath('.')
        root = db_root['test'] = Root('test', root_path)
    else:
        root = db_root['test']

    args.func(root, args)
    db_conn.close()

if __name__ == '__main__':
    main()
