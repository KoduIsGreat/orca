class OrcaError(Exception):
    pass


class ConfigurationError(OrcaError):
    pass


class ExecutionError(OrcaError):
    pass


class LedgerError(OrcaError):
    pass
