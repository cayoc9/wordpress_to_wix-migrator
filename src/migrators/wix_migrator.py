"""
Wix API helper functions for WordPress → Wix migration.

This module implements low-level interactions with the Wix REST API.
Functions defined here perform media uploads via the two-step
``/upload/url`` and ``/upload/complete`` endpoints, manage blog
taxonomies (tags and categories), create draft posts with rich
content, and publish drafts.  A simple rate limiter is included to
respect Wix's limit of roughly 200 requests per minute per site.  A
generic retry wrapper is provided to handle transient network errors
and server-side rate limiting responses (429 or 5xx).

Usage example::

    from src.extractors.wordpress_extractor import extract_posts_from_csv
    from src.parsers.ricos_parser import convert_html_to_ricos, strip_html_nodes
    from src.migrators.wix_migrator import (
        upload_image_from_url, get_or_create_terms, create_draft_post, publish_post
    )

    cfg = {"site_id": ..., "api_key": ..., "base_url": "https://www.wixapis.com"}
    posts = extract_posts_from_csv("posts.csv")
    for post in posts:
        ricos = convert_html_to_ricos(post["ContentHTML"])
        # upload cover image if present
        if post.get("FeaturedImageUrl"):
            post["FeaturedImageUrl"] = upload_image_from_url(cfg, post["FeaturedImageUrl"])
        post["CategoryIds"] = get_or_create_terms(cfg, "categories", post.get("Categories"))
        post["TagIds"] = get_or_create_terms(cfg, "tags", post.get("Tags"))
        resp = create_draft_post(cfg, post, ricos)
        draft_id = resp["post"]["id"]
        publish_post(cfg, draft_id)

"""

from __future__ import annotations

import json
import time
from typing import Callable, Dict, Iterable, List, Optional

import requests

###############################################################################
# Rate limiting and retry utilities
###############################################################################

class RateLimiter:
    """
    Simple time-based rate limiter.  Ensures that no more than ``rpm``
    requests are dispatched per minute.  The limiter is used by all
    network calls in this module to avoid hitting Wix's documented
    throughput limits.
    """

    def __init__(self, rpm: int = 200) -> None:
        self.rpm = max(1, rpm)
        self.interval = 60.0 / float(self.rpm)
        self._last = 0.0

    def wait(self, time_fn: Callable[[], float] = time.time, sleep_fn: Callable[[float], None] = time.sleep) -> None:
        now = time_fn()
        dt = now - self._last
        if dt < self.interval:
            sleep_fn(self.interval - dt)
        self._last = time_fn()


def wix_headers(cfg: Dict[str, str]) -> Dict[str, str]:
    """
    Construct the default headers required for Wix API requests.

    :param cfg: A configuration dictionary with keys ``api_key`` and
                ``site_id``.
    :return: A dictionary of headers including Authorization and
             wix-site-id.
    """
    return {
        "Authorization": cfg["api_key"],
        "wix-site-id": cfg["site_id"],
    }


def with_retries(fn: Callable[[], requests.Response], *, max_attempts: int = 5, base_delay: float = 0.7) -> requests.Response:
    """
    Execute a function returning a ``requests.Response``, retrying on
    transient HTTP errors.  Retries are attempted on status codes 429
    (too many requests) and 5xx server errors.  Backoff uses an
    exponential strategy with jitter.

    :param fn: A zero-argument callable that performs the HTTP request.
    :param max_attempts: Maximum number of attempts before giving up.
    :param base_delay: Base delay in seconds for exponential backoff.
    :return: The successful ``requests.Response``.
    :raises requests.HTTPError: if all attempts fail.
    """
    attempt = 0
    while True:
        try:
            resp = fn()
            resp.raise_for_status()
            return resp
        except requests.HTTPError as e:
            status = e.response.status_code
            if status not in (429, 500, 502, 503, 504) or attempt >= max_attempts - 1:
                raise
            # Use Retry-After header if provided, otherwise exponential backoff
            retry_after = e.response.headers.get("Retry-After")
            if retry_after:
                wait = float(retry_after)
            else:
                wait = base_delay * (2 ** attempt)
            time.sleep(wait)
            attempt += 1
        except requests.RequestException:
            if attempt >= max_attempts - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))
            attempt += 1


###############################################################################
# Media upload helpers
###############################################################################

_limiter = RateLimiter(180)  # Use a conservative default


def create_upload_url(cfg: Dict[str, str], filename: str, mime_type: str) -> Dict[str, str]:
    """
    Request a signed upload URL from Wix.  The signed URL is valid for
    one use and is used to PUT the file contents directly to Wix storage.

    :param cfg: Wix configuration dictionary.
    :param filename: Name of the file to be uploaded.
    :param mime_type: MIME type of the file (e.g., 'image/jpeg').
    :return: A dictionary containing keys ``uploadUrl`` and ``uploadToken``.
    """
    _limiter.wait()
    def do_request() -> requests.Response:
        return requests.post(
            f"{cfg['base_url']}/media/v1/files/upload/url",
            headers={**wix_headers(cfg), "Content-Type": "application/json"},
            json={"fileName": filename, "mimeType": mime_type},
        )
    resp = with_retries(do_request)
    return resp.json()


def upload_bytes_to_signed_url(url: str, data: bytes, mime_type: str) -> None:
    """
    Upload binary data to a Wix-signed URL.  This step does not use the
    Wix API; instead, it performs a direct PUT against the provided
    pre-signed URL.

    :param url: The signed upload URL returned by :func:`create_upload_url`.
    :param data: The raw bytes of the file to upload.
    :param mime_type: The MIME type to use in the Content-Type header.
    :raises requests.HTTPError: if the PUT fails.
    """
    # No rate limiting needed for the PUT request – it goes directly to Wix
    resp = requests.put(url, data=data, headers={"Content-Type": mime_type})
    resp.raise_for_status()


def finalize_upload(cfg: Dict[str, str], upload_token: str) -> Dict[str, str]:
    """
    Notify Wix that the upload has completed, returning metadata about the
    uploaded file.

    :param cfg: Wix configuration dictionary.
    :param upload_token: The token returned by :func:`create_upload_url`.
    :return: A JSON object describing the uploaded file, including its URL.
    """
    _limiter.wait()
    def do_request() -> requests.Response:
        return requests.post(
            f"{cfg['base_url']}/media/v1/files/upload/complete",
            headers={**wix_headers(cfg), "Content-Type": "application/json"},
            json={"uploadToken": upload_token},
        )
    resp = with_retries(do_request)
    return resp.json()


def upload_image_from_url(cfg: Dict[str, str], image_url: str) -> Optional[str]:
    """
    Download an image from a remote URL and upload it to Wix Media Manager.

    This helper performs all three steps (generate upload URL, PUT data,
    finalize upload).  On success it returns the Wix-hosted URL of the
    uploaded image.  Failures are logged and ``None`` is returned.

    :param cfg: Wix configuration dictionary.
    :param image_url: The source URL of the image.
    :return: The Wix URL of the uploaded file, or ``None`` on error.
    """
    if not image_url:
        return None
    try:
        # Download the image data
        r = requests.get(image_url, stream=True, timeout=30)
        r.raise_for_status()
        data = r.content
        # Determine a filename and MIME type; fallback to .jpg if unknown
        filename = image_url.split("/")[-1].split("?")[0] or "image.jpg"
        mime_type = r.headers.get("Content-Type", "image/jpeg")
        upload_info = create_upload_url(cfg, filename, mime_type)
        upload_bytes_to_signed_url(upload_info["uploadUrl"], data, mime_type)
        completed = finalize_upload(cfg, upload_info["uploadToken"])
        # Prefer the URL in the completed payload, falling back to the ID
        file_obj = completed.get("file", {})
        return file_obj.get("url") or file_obj.get("id")
    except Exception:
        return None


###############################################################################
# Taxonomy helpers
###############################################################################

def get_or_create_terms(cfg: Dict[str, str], kind: str, labels: Iterable[str]) -> List[str]:
    """
    Ensure that the given tag or category labels exist in Wix and return
    their IDs.  This function first lists existing terms from Wix and
    then creates any missing terms.

    :param cfg: Wix configuration dictionary.
    :param kind: Either ``"tags"`` or ``"categories"``.
    :param labels: An iterable of term names (strings).
    :return: A list of term IDs corresponding to the supplied labels.
    """
    ids: List[str] = []
    labels = [label.strip() for label in labels if label and label.strip()]
    if not labels:
        return ids
    base = f"{cfg['base_url']}/blog/v3/{kind}"
    # Retrieve existing terms
    _limiter.wait()
    def list_terms() -> requests.Response:
        return requests.get(base, headers=wix_headers(cfg))
    try:
        resp = with_retries(list_terms)
        existing = resp.json().get(kind, [])
        term_map = { (t.get("label") or "").lower(): t.get("id") for t in existing }
    except Exception:
        term_map = {}
    for label in labels:
        low = label.lower()
        if low in term_map:
            ids.append(term_map[low])
        else:
            # Create a new term
            _limiter.wait()
            def create() -> requests.Response:
                payload = {"label": label} if kind == "tags" else {"category": {"label": label}}
                return requests.post(base, headers={**wix_headers(cfg), "Content-Type": "application/json"}, json=payload if kind == "tags" else {"category": {"label": label}})
            try:
                resp = with_retries(create)
                obj = resp.json().get("tag" if kind == "tags" else "category", {})
                term_id = obj.get("id")
                if term_id:
                    ids.append(term_id)
                    term_map[low] = term_id
            except Exception:
                continue
    return ids


###############################################################################
# Draft and publish helpers
###############################################################################

def create_draft_post(cfg: Dict[str, str], post: Dict[str, Any], ricos: Dict[str, Any], *, allow_html_iframe: bool = True) -> Dict[str, Any]:
    """
    Create a draft blog post in Wix using the provided rich content.

    The ``post`` dictionary should include at least ``Title``, ``Slug``,
    optional ``Excerpt``, ``FeaturedImageUrl``, ``CategoryIds`` and
    ``TagIds``, plus SEO metadata (``MetaTitle``, ``MetaDescription``).

    :param cfg: Wix configuration dictionary.
    :param post: Normalized post dictionary.
    :param ricos: Rich content object returned by
                  :func:`src.parsers.ricos_parser.convert_html_to_ricos`.
    :param allow_html_iframe: Whether to allow ``type: "html"`` nodes in
                              the payload.  If the Wix API rejects
                              HTML nodes, call this function again
                              with ``allow_html_iframe=False`` and a
                              stripped version of the rich content.
    :return: The response payload from Wix describing the newly created draft.
    :raises requests.HTTPError: on failure.
    """
    api_url = f"{cfg['base_url']}/blog/v3/drafts/posts"
    # Assemble the draft post payload
    body: Dict[str, Any] = {
        "post": {
            "title": post.get("Title") or "",
            "richContent": ricos,
            "excerpt": (post.get("Excerpt") or "")[:3000],
            "coverMedia": None,
            "categoryIds": post.get("CategoryIds", []),
            "tagIds": post.get("TagIds", []),
            "seoSlug": post.get("Slug") or "",
            "seoData": {
                "title": post.get("MetaTitle") or post.get("Title") or "",
                "description": (post.get("MetaDescription") or post.get("Excerpt") or "")[:156],
            },
        }
    }
    # Cover image
    if post.get("FeaturedImageUrl"):
        body["post"]["coverMedia"] = {"image": {"src": post["FeaturedImageUrl"]}}

    _limiter.wait()
    def do_request() -> requests.Response:
        return requests.post(
            api_url,
            headers={**wix_headers(cfg), "Content-Type": "application/json"},
            data=json.dumps(body),
        )
    try:
        resp = with_retries(do_request)
        return resp.json()
    except requests.HTTPError as e:
        # If we allowed HTML and the Wix API rejects the request (400) we
        # rethrow and let the caller decide whether to strip HTML and retry.
        raise


def publish_post(cfg: Dict[str, str], draft_id: str) -> Dict[str, Any]:
    """
    Publish a draft post by its ID.

    :param cfg: Wix configuration dictionary.
    :param draft_id: The ID of the draft to publish.
    :return: The response payload from Wix describing the published post.
    :raises requests.HTTPError: on failure.
    """
    api_url = f"{cfg['base_url']}/blog/v3/drafts/posts/{draft_id}/publish"
    _limiter.wait()
    def do_request() -> requests.Response:
        return requests.post(api_url, headers=wix_headers(cfg))
    resp = with_retries(do_request)
    return resp.json()