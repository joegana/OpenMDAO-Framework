import cStringIO, StringIO
import sys

from openmdao.main.interfaces import implements, ICaseRecorder

class DumpCaseRecorder(object):
    """Dumps cases in a "pretty" form to a file-like object called "out"
    (defaults to ``sys.stdout``).  If out is None, cases will be ignored.
    """
    
    implements(ICaseRecorder)
    
    def __init__(self, out=sys.stdout):
        self.out = out

    def startup(self):
        """ Nothing needed for a dumpcase."""
        pass
        
    def record(self, case):
        """Dump the given Case in a "pretty" form."""
        if self.out:  # if self.out is None, just do nothing
            self.out.write(str(case))

    def close(self):
        """Closes `out` unless it's ``sys.stdout`` or ``sys.stderr``.
        Note that a closed recorder will do nothing in :meth:`record`."""
        if self.out is not None and self.out is not sys.stdout \
                                and self.out is not sys.stderr:
            if not isinstance(self.out,
                              (StringIO.StringIO, cStringIO.OutputType)):
                # Closing a StringIO deletes its contents.
                self.out.close()
            self.out = None

    def get_attributes(self, io_only=True):
        """ We need a custom get_attributes because we aren't using Traits to
        manage our changeable settings. This is unfortunate and should be
        changed to something that automates this somehow."""
        
        attrs = {}
        attrs['type'] = type(self).__name__
        
        return attrs
