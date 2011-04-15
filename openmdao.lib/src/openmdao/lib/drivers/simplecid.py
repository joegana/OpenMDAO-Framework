""" A simple driver that runs cases from a CaseIterator and records them
with a CaseRecorder """

# pylint: disable-msg=E0611,F0401
from openmdao.main.api import Driver
from openmdao.main.interfaces import ICaseIterator, ICaseRecorder
from openmdao.lib.datatypes.api import Instance

class SimpleCaseIterDriver(Driver):
    """
    A Driver that sequentially runs a set of cases provided by an :class:`ICaseIterator`
    and records the results in a :class:`CaseRecorder`. This is
    intended for test cases or very simple models only. For a more full-featured Driver 
    with similar functionality, see
    :class:`CaseIteratorDriver`.

    - The `iterator` socket provides the cases to be evaluated.
    - The `recorder` socket is used to record results.
    
    For each case coming from the `iterator`, the workflow will
    be executed once.
    """

    # pylint: disable-msg=E1101
    iterator = Instance(ICaseIterator, desc='Source of Cases.', required=True)
    recorder = Instance(ICaseRecorder, desc='Where Case results are recorded.',
                        required=True)
    
    def __init__(self, *args, **kwargs):
        super(SimpleCaseIterDriver, self).__init__(*args, **kwargs)
        self._iter = None  # Set to None when iterator is empty.
        self.on_trait_change(self._iterator_modified, 'iterator')

    def _iterator_modified(self, obj, name, value):
        self._call_execute = True
    
    def execute(self):
        """ Run each case in `iterator` and record results in `recorder`. """
        for case in self.iterator.get_iter():
            self._run_case(case)
            self.recorder.record(case)

    def _run_case(self, case):
        msg = None
        case.parent_id = self._case_id
        case.apply_inputs(self.parent)
        try:
            self.workflow.run(case_id=str(case.ident))
        except Exception as err:
            msg = str(err)
        try:
            case.update_outputs(self.parent, msg)
        except Exception as err:
            case.msg = msg + " : " + str(err)

