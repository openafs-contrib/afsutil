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

"""Common system utilities."""

import logging
import os
import subprocess
import sys
import six

logger = logging.getLogger(__name__)

class RingBuffer:
    """Circular array for appending."""
    # Adapted from the python cookbook.
    def __init__(self, size_max):
        self.size_max = size_max
        self.data = []

    class __FullBuffer:
        def append(self, x):
            """Append an element overwriting the oldest one."""
            self.data[self.cursor] = x
            self.cursor = (self.cursor + 1) % self.size_max

        def get(self):
            """Return list of elements in correct order."""
            return self.data[self.cursor:] + self.data[:self.cursor]

    def append(self,x):
        """Append an element at the end of the buffer."""
        self.data.append(x)
        if len(self.data) == self.size_max:
            # We are full; switch to the circular functions.
            self.cursor = 0
            self.__class__ = self.__FullBuffer

    def get(self):
        """ Return a list of elements from the oldest to the newest. """
        return self.data


class CommandMissing(Exception):
    """Command not found."""

class CommandFailed(Exception):
    """Command exited with a non-zero exit code."""
    def __init__(self, args, code, out):
        self.cmd = subprocess.list2cmdline(args)
        self.args = args
        self.code = code
        self.out = out

    def __str__(self):
        msg = "Command failed! %s; code=%d, out='%s'" % \
              (self.cmd, self.code, self.out.strip())
        return repr(msg)

def which(program, extra_paths=None, raise_errors=False):
    """Find a program in the PATH.

    program: program name or program full path
    extra_paths: list of paths to search in addition to PATH
    raise_errors: raise an exception if not found (default: False)
    """
    if not isinstance(program, six.string_types):
        raise ValueError("which() requires a string argument")
    dirname,basename = os.path.split(program)
    if dirname:
        # Full path was given; verify it is an executable file.
        if os.path.isfile(program) and os.access(program, os.X_OK):
            return program
        if raise_errors:
            raise CommandMissing("Program '%s' is not an executable file." % (program))
    else:
        # Just the basename was given; search the paths.
        paths = os.environ['PATH'].split(os.pathsep)
        if extra_paths:
            paths = paths + extra_paths
        for path in paths:
            path = path.strip('"')
            fpath = os.path.join(path, program)
            if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
                return fpath
        if raise_errors:
            raise CommandMissing("Could not find '%s' in paths %s" % (program, ":".join(paths)))
    return None

def file_should_exist(path, description=None):
    """Fails if the given file does not exist."""
    if not os.path.isfile(path):
        if description is None:
            description = "File '%s' does not exist." % (path)
        raise AssertionError(description)
    return True

def directory_should_exist(path, description=None):
    """Fails if the given directory does not exist."""
    if not os.path.isdir(path):
        if description is None:
            description = "Directory '%s' does not exist." % (path)
        raise AssertionError(description)
    return True

def directory_should_not_exist(path, description=None):
    """Fails if the given directory does exist."""
    if os.path.exists(path):
        if description is None:
            description = "Directory '%s' already exists." % (path)
        raise AssertionError(description)
    return True

def path_join(a, *p):
    # os.path.join() is brain dead.
    p = [x.lstrip('/') for x in p]
    return os.path.join(a, *p)

def nproc():
    """Return the number of processing units."""
    try:
        from sh import nproc
        return int(str(nproc()))
    except:
        return 1  # default

def mkdirp(path):
    """Make a directory with parents."""
    # Do not raise an execption if the directory already exists.
    if not os.path.isdir(path):
        os.makedirs(path)

def cat(files, path):
    """Combine one or more files."""
    dst = open(path, 'w')
    for f in files:
        with open(f, 'r') as src:
            dst.write(src.read())
    dst.close()

def touch(path):
    """Touch a file; create a empty file if not already existing."""
    with open(path, 'a'):
        os.utime(path, None)

def symlink(src, dst):
    """Create a symlink dst to src."""
    logger.debug("Creating symlink %s -> %s", dst, src)
    if not os.path.isfile(src):
        raise AssertionError("Failed to make symlink: src %s not found" % (src))
    if os.path.exists(dst) and not os.path.islink(dst):
        raise AssertionError("Failed to make symlink: dst %s exists" % (dst))
    if os.path.islink(dst):
        os.remove(dst)
    os.symlink(src, dst)
