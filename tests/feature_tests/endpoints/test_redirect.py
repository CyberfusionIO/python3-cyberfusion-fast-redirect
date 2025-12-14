import pytest
from starlette.testclient import TestClient

REDIRECT_REQUEST_OPTS = {"follow_redirects": False}

HEADERS_301_KEEP_ALL = {"Host": "301-keep-all.com"}
HEADERS_302_KEEP_NONE = {"Host": "302-keep-none.com"}
HEADERS_303_KEEP_ALL = {"Host": "303-keep-all.com"}
HEADERS_307_KEEP_ALL = {"Host": "307-keep-all.com"}
HEADERS_308_KEEP_ALL = {"Host": "308-keep-all.com"}

DEFAULT_PATH_PARAMS = [
    ("/we/might/or/might/not/keep/this/path"),
    ("we/might/or/might/not/keep/this/path"),
]

# Error handling


def test_redirect_domain_not_exists(test_client: TestClient) -> None:
    """Test response when the domain doesn't exist in the database."""
    response = test_client.get("/", headers={"Host": "domlimev.nl"})
    assert response.status_code == 400
    assert response.json() == {"detail": "No redirect exists for this domain."}


def test_redirect_domain_invalid(test_client: TestClient) -> None:
    """Test response when the domain is invalid."""
    response = test_client.get("/", headers={"Host": "123"})
    assert response.status_code == 200
    assert response.json() == {"detail": "It seems like I'm alive."}


def test_redirect_domain_empty(test_client: TestClient) -> None:
    """Test response when the domain is empty."""
    response = test_client.get("/", headers={"Host": ""})
    assert response.status_code == 400
    assert response.json() == {"detail": "Specify redirect to look for."}


def test_redirect_domain_invalid_destination_url(
    test_client: TestClient,
) -> None:
    """Test response when the destination URL is invalid."""
    response = test_client.get("/", headers={"Host": "301-invalid-destination-url.com"})
    assert response.status_code == 500
    assert response.json() == {
        "detail": "The destination URL for this redirect is invalid."
    }


def test_redirect_domain_invalid_status_code(
    test_client: TestClient,
) -> None:
    """Test response when the status code is invalid."""
    response = test_client.get("/", headers={"Host": "200-invalid-status-code.com"})
    assert response.status_code == 500
    assert response.json() == {
        "detail": "The status code for this redirect is invalid."
    }


def test_redirect_domain_x_redirect_by_header(test_client: TestClient) -> None:
    """Test that response has X-Redirect-By header, and its value."""
    response = test_client.get(
        "/", headers=HEADERS_301_KEEP_ALL, **REDIRECT_REQUEST_OPTS
    )
    assert response.headers["x-redirect-by"] == "fast-redirect"


# Edge cases


def test_redirect_domain_case_insensitive(
    test_client: TestClient,
) -> None:
    """Test that lowercase version of domain matches non-lowercase domain in database."""
    response = test_client.get(
        "/",
        headers={"Host": "301-uppercase-domain.com"},
        **REDIRECT_REQUEST_OPTS,
    )
    assert response.status_code == 301
    assert response.headers["location"] == "https://nos.nl"


def test_redirect_domain_wildcard(
    test_client: TestClient,
) -> None:
    """Test that domain is matched to redirect for wildcard domain."""
    response = test_client.get(
        "/",
        headers={"Host": "test.301-wildcard.com"},
        **REDIRECT_REQUEST_OPTS,
    )
    assert response.status_code == 301
    assert response.headers["location"] == "https://fd.nl"


# Path


@pytest.mark.parametrize("path", DEFAULT_PATH_PARAMS)
def test_redirect_domain_keep_path(path: str, test_client: TestClient) -> None:
    """Test that path is kept."""
    response = test_client.get(
        path, headers=HEADERS_301_KEEP_ALL, **REDIRECT_REQUEST_OPTS
    )
    assert (
        response.headers["location"]
        == "https://nos.nl/we/might/or/might/not/keep/this/path"
    )


@pytest.mark.parametrize("path", DEFAULT_PATH_PARAMS)
def test_redirect_domain_discard_path(path: str, test_client: TestClient) -> None:
    """Test that path is discarded."""
    response = test_client.get(
        path, headers=HEADERS_302_KEEP_NONE, **REDIRECT_REQUEST_OPTS
    )
    assert response.headers["location"] == "https://nu.nl"


# Query parameters


def test_redirect_domain_keep_query_parameters(
    test_client: TestClient,
) -> None:
    """Test that query parameters are kept."""
    response = test_client.get(
        "/?a=b", headers=HEADERS_301_KEEP_ALL, **REDIRECT_REQUEST_OPTS
    )
    assert response.headers["location"] == "https://nos.nl?a=b"


def test_redirect_domain_discard_query_parameters(
    test_client: TestClient,
) -> None:
    """Test that query parameters are discarded."""
    response = test_client.get(
        "/?a=b", headers=HEADERS_302_KEEP_NONE, **REDIRECT_REQUEST_OPTS
    )
    assert response.headers["location"] == "https://nu.nl"


def test_redirect_domain_keep_destination_url_query_parameters(
    test_client: TestClient,
) -> None:
    """Test that query parameters from the destination URL are kept."""
    response = test_client.get(
        "/?a=b",
        headers={"Host": "301-query-parameter-in-destination-url.com"},
        **REDIRECT_REQUEST_OPTS,
    )
    assert response.headers["location"] == "https://nos.nl?e=f&a=b"


# Path and query parameters


def test_redirect_domain_keep_path_and_query_parameters(
    test_client: TestClient,
) -> None:
    """Test that path and query parameters are kept."""
    response = test_client.get(
        "/we/might/or/might/not/keep/this/path?a=b",
        headers=HEADERS_301_KEEP_ALL,
        **REDIRECT_REQUEST_OPTS,
    )
    assert (
        response.headers["location"]
        == "https://nos.nl/we/might/or/might/not/keep/this/path?a=b"
    )


def test_redirect_domain_discard_path_and_query_parameters(
    test_client: TestClient,
) -> None:
    """Test that path and query parameters are discarded."""
    response = test_client.get(
        "/we/might/or/might/not/keep/this/path?a=b",
        headers=HEADERS_302_KEEP_NONE,
        **REDIRECT_REQUEST_OPTS,
    )
    assert response.headers["location"] == "https://nu.nl"


# Status codes


def test_redirect_domain_301_status_code(test_client: TestClient) -> None:
    """Test that correct 301 status code is returned."""
    response = test_client.get(
        "/", headers=HEADERS_301_KEEP_ALL, **REDIRECT_REQUEST_OPTS
    )
    assert response.status_code == 301


def test_redirect_domain_302_status_code(test_client: TestClient) -> None:
    """Test that correct 302 status code is returned."""
    response = test_client.get(
        "/", headers=HEADERS_302_KEEP_NONE, **REDIRECT_REQUEST_OPTS
    )
    assert response.status_code == 302


def test_redirect_domain_303_status_code(test_client: TestClient) -> None:
    """Test that correct 303 status code is returned."""
    response = test_client.get(
        "/", headers=HEADERS_303_KEEP_ALL, **REDIRECT_REQUEST_OPTS
    )
    assert response.status_code == 303


def test_redirect_domain_307_status_code(test_client: TestClient) -> None:
    """Test that correct 307 status code is returned."""
    response = test_client.get(
        "/", headers=HEADERS_307_KEEP_ALL, **REDIRECT_REQUEST_OPTS
    )
    assert response.status_code == 307


def test_redirect_domain_308_status_code(test_client: TestClient) -> None:
    """Test that correct 308 status code is returned."""
    response = test_client.get(
        "/", headers=HEADERS_308_KEEP_ALL, **REDIRECT_REQUEST_OPTS
    )
    assert response.status_code == 308
