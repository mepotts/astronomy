"""Loud-failure stand-in for sksparse.cholmod (see package __init__)."""


class CholmodError(Exception):
    pass


def _refuse(*_a, **_k):
    raise RuntimeError(
        "sksparse shim: sparse CHOLMOD is NOT available in this environment "
        "(WSL without sudo; libsuitesparse-dev missing). You have hit a code "
        "path outside the validated M1 stack (sparse Sigma solve for common "
        "signals / MarginalizingTimingModel / ConditionalGP). Install real "
        "scikit-sparse against system SuiteSparse before using this path."
    )


def cholesky(*a, **k):
    _refuse()


def cholesky_AAt(*a, **k):
    _refuse()


def analyze(*a, **k):
    _refuse()
