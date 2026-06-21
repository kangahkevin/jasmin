from jasmin.tools.singleton import Singleton


class CompiledNode(metaclass=Singleton):
    """A compiled code holder singleton"""

    def __init__(self):
        self.nodes = {}

    def get(self, pyCode):
        """Return a compiled pyCode object or instanciate a new one"""
        if pyCode not in self.nodes:
            self.nodes[pyCode] = compile(pyCode, '', 'exec')

        return self.nodes[pyCode]
