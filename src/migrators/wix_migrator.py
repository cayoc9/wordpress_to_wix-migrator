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
        ricos = convert_html_to_ricos(cfg, post["ContentHTML"])
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
from typing import Callable, Dict, Iterable, List, Optional, Any

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

    :param cfg: A configuration dictionary with the ``access_token``.
    :return: A dictionary of headers including Authorization.
    """
    api_key = cfg.get("api_key") or cfg.get("apiKey") or ""
    access_token = cfg.get("access_token") or cfg.get("accessToken") or ""
    headers: Dict[str, str] = {}
    if api_key:
        # API Keys use raw value in Authorization header (no Bearer prefix)
        headers["Authorization"] = api_key
    elif access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    # Add site-scoped header when available. Many Wix REST endpoints require it.
    site_id = cfg.get("site_id") or cfg.get("wix_site_id") or cfg.get("siteId")
    if site_id:
        headers["wix-site-id"] = site_id
    account_id = cfg.get("account_id") or cfg.get("wix_account_id") or cfg.get("accountId")
    if account_id:
        headers["wix-account-id"] = account_id
    return headers


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
# Member helpers
###############################################################################

def list_members(cfg: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Lists all members for the Wix site.

    :param cfg: Wix configuration dictionary with an ``access_token``.
    :return: A list of member objects.
    """
    _limiter.wait()
    def do_request() -> requests.Response:
        return requests.get(
            f"{cfg['base_url']}/members/v1/members",
            headers=wix_headers(cfg),
        )
    try:
        resp = with_retries(do_request)
        return resp.json().get("members", [])
    except requests.HTTPError as e:
        print(f"Failed to list members: {e.response.text}")
        return []

def create_member(cfg: Dict[str, str], email: str) -> Optional[Dict[str, Any]]:
    """
    Creates a new member on the Wix site.

    :param cfg: Wix configuration dictionary with an ``access_token``.
    :param email: The email address for the new member.
    :return: The new member object, or ``None`` on failure.
    """
    _limiter.wait()
    def do_request() -> requests.Response:
        return requests.post(
            f"{cfg['base_url']}/members/v1/members",
            headers={**wix_headers(cfg), "Content-Type": "application/json"},
            json={"member": {"loginEmail": email}},
        )
    try:
        resp = with_retries(do_request)
        return resp.json().get("member")
    except requests.HTTPError as e:
        print(f"Failed to create member: {e.response.text}")
        # Re-raise the exception so it can be handled upstream
        raise


def query_member_by_email(cfg: Dict[str, str], email: str) -> Optional[Dict[str, Any]]:
    """
    Queries for a member by their login email using the v1/members/query endpoint.

    :param cfg: Wix configuration dictionary.
    :param email: The email to query for.
    :return: The member object if found, otherwise None.
    """
    _limiter.wait()
    query = {
        "query": {
            "filter": {
                "loginEmail": email
            }
        }
    }
    def do_request() -> requests.Response:
        return requests.post(
            f"{cfg['base_url']}/members/v1/members/query",
            headers={**wix_headers(cfg), "Content-Type": "application/json"},
            json=query,
        )
    try:
        resp = with_retries(do_request)
        members = resp.json().get("members", [])
        if members:
            return members[0]  # Return the first member found
        return None
    except requests.HTTPError as e:
        print(f"Failed to query member by email {email}: {e.response.text}")
        return None


###############################################################################
# Media upload helpers
###############################################################################

_limiter = RateLimiter(180)  # Use a conservative default





def import_image_from_url(cfg: Dict[str, str], image_url: str) -> Optional[str]:
    """
    Importa uma imagem de uma URL remota para o Gerenciador de Mídia do Wix.

    Esta função utiliza o endpoint Import File, que é a maneira recomendada
    de adicionar mídia externa ao Wix.

    :param cfg: Dicionário de configuração do Wix.
    :param image_url: A URL de origem da imagem.
    :return: O ID de mídia do Wix do arquivo importado, ou ``None`` em caso de erro.
    """
    if not image_url:
        return None
    
    _limiter.wait()
    
    def do_request() -> requests.Response:
        return requests.post(
            f"{cfg['base_url']}/site-media/v1/files/import",
            headers={**wix_headers(cfg), "Content-Type": "application/json"},
            json={"url": image_url, "mediaType": "IMAGE"},
        )
    
    try:
        resp = with_retries(do_request)
        file_obj = resp.json().get("file", {})
        return file_obj.get("id")
    except Exception as e:
        print(f"Failed to import image from {image_url}: {e}")
        return None


###############################################################################
# Taxonomy helpers
###############################################################################

def get_or_create_terms(cfg: Dict[str, str], kind: str, labels: Iterable[str]) -> List[str]:
    """
    Garante que as etiquetas ou categorias fornecidas existam no Wix e
    retorna seus IDs. Esta função primeiro lista os termos existentes no Wix
    e, em seguida, cria quaisquer termos ausentes.

    :param cfg: Dicionário de configuração do Wix.
    :param kind: "tags" ou "categories".
    :param labels: Um iterável de nomes de termos (strings).
    :return: Uma lista de IDs de termos correspondentes às etiquetas fornecidas, sem duplicatas.
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
            term_id = term_map[low]
            # Add to ids list only if it's not already present to avoid duplicates
            if term_id not in ids:
                ids.append(term_id)
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
                    # Add to ids list only if it's not already present to avoid duplicates
                    if term_id not in ids:
                        ids.append(term_id)
                    term_map[low] = term_id
            except Exception:
                continue
    return ids


###############################################################################
# Draft and publish helpers
###############################################################################

def create_draft_post(cfg: Dict[str, str], post: Dict[str, Any], ricos: Dict[str, Any], member_id: str, *, allow_html_iframe: bool = True) -> Dict[str, Any]:
    """
    Cria um rascunho de postagem no blog no Wix usando o conteúdo rico fornecido.

    O dicionário ``post`` deve incluir pelo menos ``Title``, ``Slug``,
    opcionalmente ``Excerpt``, ``FeaturedImageUrl``, ``CategoryIds`` e
    ``TagIds``, além de metadados de SEO (``MetaTitle``, ``MetaDescription``).

    :param cfg: Dicionário de configuração do Wix.
    :param post: Dicionário normalizado da postagem.
    :param ricos: Objeto de conteúdo rico retornado por
                  :func:`src.parsers.ricos_parser.convert_html_to_ricos`.
    :param member_id: O ID do membro a ser definido como autor.
    :param allow_html_iframe: Indica se deve permitir nós ``type: "html"`` no
                              payload. Se a API do Wix rejeitar nós HTML,
                              chame esta função novamente com
                              ``allow_html_iframe=False`` e uma versão
                              sem esses nós do conteúdo rico.
    :return: O payload de resposta do Wix descrevendo o rascunho criado.
    :raises requests.HTTPError: em caso de falha.
    """
    api_url = f"{cfg['base_url']}/blog/v3/draft-posts"
    # Assemble the draft post payload
    body: Dict[str, Any] = {
        "draftPost": {
            "title": post.get("Title") or "",
            "memberId": member_id,
            "richContent": ricos,
            "excerpt": (post.get("Excerpt") or "")[:3000],
            "categoryIds": post.get("CategoryIds", []),
            "tagIds": post.get("TagIds", []),
            "slug": post.get("Slug") or "",
            "seoData": {
                "title": post.get("MetaTitle") or post.get("Title") or "",
                "description": (post.get("MetaDescription") or post.get("Excerpt") or "")[:156],
            },
        }
    }
    
    # Validate rich content structure
    if not isinstance(ricos, dict) or "nodes" not in ricos:
        print(f"WARNING: Invalid Ricos structure for post '{post.get('Title', 'Unknown')}'. Using empty content.")
        body["draftPost"]["richContent"] = {"nodes": []}
    
    # Limit the size of rich content to prevent API errors
    import json
    ricos_json = json.dumps(body["draftPost"]["richContent"])
    if len(ricos_json) > 50000:  # Limit to 50KB
        print(f"WARNING: Ricos content too large ({len(ricos_json)} bytes). Truncating...")
        # Keep only the first nodes to reduce size
        original_nodes = body["draftPost"]["richContent"]["nodes"]
        truncated_nodes = []
        current_size = 0
        
        for node in original_nodes:
            node_json = json.dumps(node)
            if current_size + len(node_json) > 45000:  # Leave some margin
                break
            truncated_nodes.append(node)
            current_size += len(node_json)
            
        body["draftPost"]["richContent"]["nodes"] = truncated_nodes
        print(f"Truncated from {len(original_nodes)} to {len(truncated_nodes)} nodes")
    # Cover image
    if post.get("FeaturedImageId"):
        body["draftPost"]["media"] = {
            "wixMedia": {
                "image": {"id": post["FeaturedImageId"]}
            },
            "displayed": True,
            "custom": True
        }

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
        print(f"Failed to create draft post. Error: {e}")
        if e.response:
            print(f"Response body: {e.response.text}")
            print(f"Request body: {json.dumps(body, indent=2)}")
        # Re-raise the exception so it can be handled upstream
        raise


def publish_post(cfg: Dict[str, str], draft_id: str) -> Dict[str, Any]:
    """
    Publish a draft post by its ID.

    :param cfg: Wix configuration dictionary.
    :param draft_id: The ID of the draft to publish.
    :return: The response payload from Wix describing the published post.
    :raises requests.HTTPError: on failure.
    """
    api_url = f"{cfg['base_url']}/blog/v3/draft-posts/{draft_id}/publish"
    _limiter.wait()
    def do_request() -> requests.Response:
        return requests.post(api_url, headers=wix_headers(cfg))
    resp = with_retries(do_request)
    return resp.json()
