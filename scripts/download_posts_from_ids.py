import argparse
import json
import os
import subprocess
import sys
import time
from typing import List, Set


def load_ids(ids_file: str) -> List[str]:
    with open(ids_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    ids = data.get("ids", [])
    # Garante strings e remove vazios
    return [str(x).strip() for x in ids if str(x).strip()]


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def fetch_post_via_script(post_id: str) -> str:
    """Executa scripts/get_wix_post.py e retorna o JSON do post via stdout."""
    proc = subprocess.run(
        [sys.executable, "scripts/get_wix_post.py", post_id],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if proc.returncode != 0:
        raise RuntimeError(f"get_wix_post.py retornou código {proc.returncode}: {proc.stderr.strip()}")

    output = proc.stdout.strip()
    if not output:
        raise RuntimeError("Saída vazia do get_wix_post.py")

    # Valida JSON básico
    try:
        json.loads(output)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Saída não é JSON válido: {e}\nTrecho: {output[:200]}...")

    return output


def save_post(out_dir: str, post_id: str, content: str) -> str:
    ensure_dir(out_dir)
    out_path = os.path.join(out_dir, f"{post_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path


def download_all(ids_file: str, out_dir: str, overwrite: bool, delay: float) -> None:
    ids = load_ids(ids_file)
    seen: Set[str] = set()

    ensure_dir(out_dir)

    total = len(ids)
    success = 0
    skipped = 0
    failures = 0

    for idx, post_id in enumerate(ids, start=1):
        if post_id in seen:
            skipped += 1
            continue
        seen.add(post_id)

        out_path = os.path.join(out_dir, f"{post_id}.json")
        if not overwrite and os.path.exists(out_path):
            print(f"[{idx}/{total}] já existe, pulando: {post_id}")
            skipped += 1
            continue

        try:
            content = fetch_post_via_script(post_id)
            save_post(out_dir, post_id, content)
            print(f"[{idx}/{total}] salvo em {out_path}")
            success += 1
        except Exception as e:
            print(f"[{idx}/{total}] falhou {post_id}: {e}")
            failures += 1

        if delay > 0:
            time.sleep(delay)

    print(
        f"Concluído. Sucesso: {success} | Pulados: {skipped} | Falhas: {failures} | Únicos: {len(seen)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Baixa todos os posts listados em um arquivo JSON de IDs, "
            "usando scripts/get_wix_post.py, e salva cada um em posts/{id}.json"
        )
    )
    parser.add_argument(
        "--ids-file",
        default="data/published_post_ids_260.json",
        help="Caminho para o JSON com a chave 'ids' (default: data/published_post_ids_260.json)",
    )
    parser.add_argument(
        "--out-dir",
        default="posts",
        help="Diretório de saída para salvar os posts (default: posts)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Sobrescreve arquivos existentes em out-dir",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Atraso em segundos entre requisições (default: 0.0)",
    )

    args = parser.parse_args()
    download_all(args.ids_file, args.out_dir, args.overwrite, args.delay)


if __name__ == "__main__":
    main()

