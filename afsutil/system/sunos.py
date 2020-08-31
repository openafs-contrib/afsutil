# Copyright (c) 2014-2017 Sine Nomine Associates
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""Solaris specific utilities."""

import logging
import os
import re
import sys
import sh

from afsutil.system import common as _mod
CommandMissing = _mod.CommandMissing
cat = _mod.cat
directory_should_exist = _mod.directory_should_exist
directory_should_not_exist = _mod.directory_should_not_exist
file_should_exist = _mod.file_should_exist
mkdirp = _mod.mkdirp
nproc = _mod.nproc
path_join = _mod.path_join
symlink = _mod.symlink
touch = _mod.touch
which = _mod.which

logger = logging.getLogger(__name__)

def get_running():
    """Get a set of running processes."""
    ps = sh.Command('/usr/bin/ps') # avoid the old BSD variant
    procs = set()
    column = None
    for line in ps('-e', '-f', _iter=True):
        line = line.rstrip()
        if column is None:
            # The first line of the `ps' output is a header line which
            # used to find the command field column.
            column = line.index('CMD')
            continue
        cmd_line = line[column:]
        if cmd_line.startswith('['):  # skip linux threads
            continue
        command = cmd_line.split()[0]
        procs.add(os.path.basename(command))
    return procs

def is_running(program):
    """Returns true if program is running."""
    return program in get_running()

def afs_mountpoint():
    mountpoint = None
    pattern = r'(/.\S+) on AFS'
    paths = os.environ.get('PATH', '').split(':')
    paths.extend(['/bin', '/sbin', '/usr/sbin'])
    mount = sh.Command('mount', search_paths=paths)
    for line in mount(_iter=True):
        found = re.search(pattern, line)
        if found:
            mountpoint = found.group(1)
    return mountpoint

def is_afs_mounted():
    """Returns true if afs is mounted."""
    return afs_mountpoint() is not None

def afs_umount():
    """Attempt to unmount afs, if mounted."""
    afs = afs_mountpoint()
    if afs:
        paths = os.environ.get('PATH', '').split(':')
        paths.extend(['/bin', '/sbin', '/usr/sbin'])
        umount = sh.Command('umount', search_paths=paths)
        umount(afs)

def network_interfaces():
    """Return list of non-loopback network interfaces."""
    try:
        command = sh.Command('ipadm')
        args = ('show-addr', '-p', '-o', 'STATE,ADDR')
        pattern = r'ok:(\d+\.\d+\.\d+\.\d+)'
    except sh.CommandNotFound:
        # Fall back to old command on old solaris releases.
        command = sh.Command('/usr/sbin/ifconfig')
        args = ('-a')
        pattern = r'inet (\d+\.\d+\.\d+\.\d+)'
    addrs = []
    for line in command(*args, _iter=True):
        match = re.match(pattern, line)
        if match:
            addr = match.group(1)
            if not addr.startswith("127."):
                addrs.append(addr)
    return addrs

def is_loaded(kmod):
    """Returns the list of currently loaded kernel modules."""
    modinfo = sh.Command('/usr/sbin/modinfo')
    for i, line in enumerate(modinfo('-w', _iter=True)):
        if i == 0:
            continue # skip header line
        # Fields are: Id Loadaddr Size Info Rev Module (Name)
        m = re.match(r'\s*(\d+)\s+\S+\s+\S+\s+\S+\s+\d+\s+(\S+)', line)
        if not m:
            raise AssertionError("Unexpected modinfo output: %s" % (line))
        mid = m.group(1)  # We will need the id to remove the module.
        mname = m.group(2)
        if kmod == mname:
            return mid
    return 0

def detect_gfind():
    return which('gfind', extra_paths=['/opt/csw/bin'])

def tar(tarball, source_path, tar=None):
    if tar is None:
        tar = 'gtar'
    tar = sh.Command(tar).bake(_in=sys.stdin, _out=sys.stdout, _err=sys.stderr)
    tar('czf', tarball, source_path)

def untar(tarball, chdir=None, tar=None):
    if tar is None:
        tar = 'gtar'
    tar = sh.Command(tar).bake(_in=sys.stdin, _out=sys.stdout, _err=sys.stderr)
    savedir = None
    if chdir:
        savedir = os.getcwd()
        os.chdir(chdir)
    try:
        tar('xzf', tarball)
    finally:
        if savedir:
            os.chdir(savedir)

def _so_symlinks(path):
    """Create shared lib symlinks."""
    if not os.path.isdir(path):
        assert AssertionError("Failed to make so symlinks: path '%s' is not a directory.", path)
    for dirent in os.listdir(path):
        fname = os.path.join(path, dirent)
        if os.path.isdir(fname) or os.path.islink(fname):
            continue
        m = re.match(r'(.+\.so)\.(\d+)\.(\d+)\.(\d+)$', fname)
        if m:
            so,x,y,z = m.groups()
            symlink(fname, "%s.%s.%s" % (so, x, y))
            symlink(fname, "%s.%s" % (so, x))
            symlink(fname, so)

def configure_dynamic_linker(path):
    crle = sh.Command('/usr/bin/crle')
    if not os.path.isdir(path):
        raise AssertionError("Failed to configure dynamic linker: path %s not found." % (path))
    _so_symlinks(path)
    crle('-u', '-l', path)
    crle('-64', '-u', '-l', path)

def unload_module():
    modunload = sh.Command('modunload')
    module_id = is_loaded('afs')
    if module_id != 0:
        modunload('-i', module_id)
