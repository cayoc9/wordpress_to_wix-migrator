from __future__ import annotations

import os
import io
import mimetypes
from pathlib import Path
from typing import Generator, Iterable, List, Optional, Union


# Importa SDK do Gemini (google-genai). Oferece mensagem clara se não estiver instalado.
try:
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore
except Exception as exc:  # pragma: no cover - feedback amigável em ambientes sem deps
    raise ImportError(
        "Pacote 'google-genai' não encontrado. Adicione-o ao ambiente (pip install google-genai)."
    ) from exc


ContentInput = Union[str, Path, bytes, "Image.Image", dict]


class GeminiClient:
    """Cliente simples para o Gemini API (Google Gen AI) com suporte multimodal.

    - Lê a chave da API de `GOOGLE_API_KEY` por padrão.
    - Aceita conteúdos de texto e imagem (paths, bytes, PIL.Image ou URIs GCS).
    - Focado em geração de conteúdo via `models.generate_content` e streaming.

    Exemplo rápido:
        from services.gemini_client import GeminiClient

        client = GeminiClient()
        result = client.generate([
            "Resuma a imagem em 1 frase:",
            "/caminho/para/imagem.jpg",
        ])
        print(result["text"])  # texto gerado

        # Streaming
        for chunk in client.generate_stream([
            "Descreva esta imagem:",
            "/caminho/para/imagem.jpg",
        ]):
            print(chunk, end="")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        http_options: Optional[dict] = None,
    ) -> None:
        # Obtém chave de API do argumento ou do ambiente
        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError(
                "Defina a variável de ambiente GOOGLE_API_KEY ou passe api_key explicitamente."
            )

        self.model = model

        # Instancia o client. O SDK aceita a key via env var; aqui passamos diretamente.
        # http_options é opcional; quando presente, o SDK aceita dict.
        if http_options:
            self.client = genai.Client(api_key=key, http_options=http_options)
        else:
            self.client = genai.Client(api_key=key)

    # ------------------------- API PÚBLICA -------------------------
    def generate(
        self,
        inputs: Iterable[ContentInput],
        *,
        model: Optional[str] = None,
    ) -> dict:
        """Gera conteúdo (não streaming) a partir de textos e/ou imagens.

        - inputs: lista contendo strings (texto), paths de imagem, bytes de imagem,
                  PIL.Image.Image, ou dicts com {"uri": str, "mime_type": str}.
        - model: opcional, sobrescreve o modelo padrão desta instância.

        Retorna dict com chaves: {"text": str, "raw": response}.
        """
        contents = self._build_contents(inputs)
        response = self.client.models.generate_content(
            model=model or self.model,
            contents=contents,
        )
        return {"text": getattr(response, "text", None), "raw": response}

    def generate_stream(
        self,
        inputs: Iterable[ContentInput],
        *,
        model: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Gera conteúdo em streaming. Faz yield de pedaços de texto conforme chegam."""
        contents = self._build_contents(inputs)
        for chunk in self.client.models.generate_content_stream(
            model=model or self.model,
            contents=contents,
        ):
            text = getattr(chunk, "text", None)
            if text:
                yield text

    # ----------------------- HELPERS INTERNOS ----------------------
    def _build_contents(self, inputs: Iterable[ContentInput]) -> List[object]:
        parts: List[object] = []

        # Importação tardia do PIL para não exigir Pillow se só texto for usado
        try:
            from PIL import Image  # type: ignore
        except Exception:
            Image = None  # type: ignore

        for item in inputs:
            # 1) Texto simples
            if isinstance(item, str):
                # Se parece um caminho existente, trataremos como arquivo; senão, como texto
                potential_path = Path(item)
                if potential_path.exists() and potential_path.is_file():
                    parts.append(self._part_from_file(potential_path))
                else:
                    parts.append(item)
                continue

            # 2) Caminho (Path)
            if isinstance(item, Path):
                parts.append(self._part_from_file(item))
                continue

            # 3) Bytes (assume imagem JPEG por padrão se não detectado)
            if isinstance(item, (bytes, bytearray)):
                mime = "image/jpeg"
                parts.append(types.Part.from_bytes(data=bytes(item), mime_type=mime))
                continue

            # 4) PIL Image
            if Image is not None:
                try:
                    if isinstance(item, Image.Image):  # type: ignore[attr-defined]
                        buf = io.BytesIO()
                        # Usa PNG para preservar transparência quando houver
                        item.save(buf, format="PNG")
                        parts.append(
                            types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png")
                        )
                        continue
                except Exception:
                    pass

            # 5) Dict URI
            if isinstance(item, dict) and {"uri", "mime_type"}.issubset(item.keys()):
                parts.append(
                    types.Part.from_uri(file_uri=item["uri"], mime_type=item["mime_type"])
                )
                continue

            raise TypeError(
                "Tipo de input não suportado em GeminiClient: " f"{type(item)!r}"
            )

        return parts

    @staticmethod
    def _part_from_file(path: Path) -> object:
        mime, _ = mimetypes.guess_type(str(path))
        if not mime:
            # fallback básico; os modelos esperam imagem com tipo válido
            mime = "image/jpeg"
        with path.open("rb") as f:
            data = f.read()
        return types.Part.from_bytes(data=data, mime_type=mime)

