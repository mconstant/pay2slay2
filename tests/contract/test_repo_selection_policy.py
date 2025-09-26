# T051 staging vs canonical repo selection (initial failing)


def select_repository(branch: str):
    if branch == "main":
        return "ghcr.io/mconstant/pay2slay-api"
    return "ghcr.io/mconstant/pay2slay-api-staging"


def test_main_goes_canonical():
    assert select_repository("main").endswith("pay2slay-api")


def test_feature_branch_not_canonical():
    repo = select_repository("feature/x")
    assert repo.endswith("-staging"), "Feature branch should select staging repo"
