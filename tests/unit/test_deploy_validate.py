import pytest

from src.lib import deploy_validate as dv


def test_repo_policy_main_canonical_ok():
    dv.ensure_repo_allowed("ghcr.io/mconstant/pay2slay-api", True)


def test_repo_policy_main_staging_fail():
    with pytest.raises(dv.RepositoryPolicyError):
        dv.ensure_repo_allowed("ghcr.io/mconstant/pay2slay-api-staging", True)


def test_feature_branch_requires_staging():
    with pytest.raises(dv.RepositoryPolicyError):
        dv.ensure_repo_allowed("ghcr.io/mconstant/pay2slay-api", False)


def test_reject_floating_tag():
    with pytest.raises(dv.FloatingTagError):
        dv.reject_floating_tag("ghcr.io/mconstant/pay2slay-api:latest")
