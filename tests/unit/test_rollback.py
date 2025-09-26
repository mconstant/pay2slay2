import os

import pytest

from src.lib import rollback


def test_rollback_build_invocation_sentinel():
    os.environ["PAY2SLAY_ROLLBACK_SENTINEL"] = "1"
    # triggering attempt_build should raise
    with pytest.raises(rollback.RollbackBuildInvocationError):
        rollback.attempt_build_during_rollback()
    os.environ.pop("PAY2SLAY_ROLLBACK_SENTINEL")
