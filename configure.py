import sys
import os
import re
import platform

def which(*alternatives):
    """Find a program in the PATH or return 'missing'."""
    for program in alternatives:
        for path in os.environ['PATH'].split(os.pathsep):
            path = os.path.join(path.strip('"'), program)
            if os.access(path, os.X_OK):
                if ' ' in path:
                    path = '"{0}"'.format(path)
                return path
    return 'missing'

def name():
    """Extract our name from the setup.py."""
    setup = open('setup.py').read()
    match = re.search(r'name=[\'\"](.*)[\'\"]', setup)
    if match:
        return match.group(1)
    raise ValueError('Package name not found in setup.py.')

def version():
    """Determine the version number from the most recent git tag."""
    version = os.popen('git describe').read() or '0.0.0'
    return version.lstrip('v').strip()

def rpm_dist():
    """Determine the rpm dist component for rhel/centos packaging."""
    name, version, id_ = platform.dist()
    if name in ('redhat', 'centos'):
        m = re.match(r'(\d+)\.', version)
        if m:
            return '.el%d' % int(m.group(1))
    return ''

def configure():
    with open('Makefile.config', 'w') as cf:
        cf.write("NAME=%s\n" % name())
        cf.write("VERSION=%s\n" % version())
        cf.write("PYTHON=%s\n" % sys.executable)
        cf.write("PYFLAKES=%s\n" % which('pyflakes'))
        pip = which('pip', 'pip2')
        cf.write("PIP=%s\n" % pip)
        install = 'setup' if pip == 'missing' else 'pip'
        cf.write("INSTALL=%s\n" % install)
        cf.write("RPM_DIST=%s\n" % rpm_dist())

if __name__ == '__main__':
    configure()
