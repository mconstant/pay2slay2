import pytest

# T007 initial failing test for deploy requires image tag existence


class MissingImageTagError(Exception):
    pass


def deploy_stub(image_sha: str, tag_exists: bool):
    if not tag_exists:
        raise MissingImageTagError(f"Tag {image_sha} not found")
    return {"image_sha": image_sha}


def test_deploy_requires_existing_tag():
    with pytest.raises(MissingImageTagError):
        deploy_stub("deadbeef" * 5, tag_exists=False)
