#!/usr/bin/env node
"use strict";

/**
 * Script de atualização de posts do Wix Blog (draft → update → publish).
 *
 * Pré-requisitos:
 * - Node 18+ (fetch nativo)
 * - Variáveis de ambiente:
 *   - WIX_API_KEY: API Key (escopos: wix-blog.manage-posts)
 *   - WIX_SITE_ID: ID do site Wix alvo
 *
 * Uso:
 *   node scripts/update_wix_post.js \
 *     --post-id <uuid> \
 *     --file data/posts/774b42ef-b746-4b6f-8239-4e6f3f39841f.json \
 *     [--publish]
 *
 * Observações importantes sobre fluxo e revision:
 * - O ID do post permanece estável entre rascunho e publicado.
 * - Para editar um post publicado, crie (ou garanta) um rascunho, atualize o rascunho e publique.
 * - A API usa controle otimista por revision; ao atualizar, envie a revision atual para evitar sobrescrita concorrente.
 */

const fs = require("fs");
const path = require("path");

// Config
const BASE_URL = "https://www.wixapis.com/blog/v3"; // host REST do Wix Blog

function die(msg, code = 1) {
  console.error(msg);
  process.exit(code);
}

function parseArgs(argv) {
  const args = { publish: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--post-id") args.postId = argv[++i];
    else if (a === "--file") args.file = argv[++i];
    else if (a === "--publish") args.publish = true;
    else if (a === "-h" || a === "--help") args.help = true;
    else die(`Argumento desconhecido: ${a}`);
  }
  return args;
}

function usage() {
  return `
Atualiza um post do Wix Blog usando a API REST.

Uso:
  node scripts/update_wix_post.js --post-id <uuid> --file <caminho.json> [--publish]

Variáveis de ambiente:
  WIX_API_KEY  API Key com escopo wix-blog.manage-posts
  WIX_SITE_ID  ID do site Wix (Site Dashboard > Settings > Advanced > API Keys)

Comportamento:
  1) Busca o post e coleta a revision.
  2) Garante rascunho (se já está publicado, cria/ativa rascunho).
  3) Atualiza campos presentes no arquivo JSON (p.ex. richContent, title, excerpt...).
  4) Se --publish, publica o rascunho atualizado.
`;
}

async function wixFetch(url, options = {}) {
  const apiKey = process.env.WIX_API_KEY;
  const siteId = process.env.WIX_SITE_ID;
  if (!apiKey) die("WIX_API_KEY não definido no ambiente.");
  if (!siteId) die("WIX_SITE_ID não definido no ambiente.");

  const headers = Object.assign(
    {
      "Authorization": apiKey,
      "wix-site-id": siteId,
      "Content-Type": "application/json",
    },
    options.headers || {}
  );

  const res = await fetch(url, { ...options, headers });
  let bodyText = "";
  try { bodyText = await res.text(); } catch {}
  let json;
  try { json = bodyText ? JSON.parse(bodyText) : undefined; } catch {
    json = undefined;
  }
  if (!res.ok) {
    const msg = json?.message || res.statusText || "Erro HTTP";
    const details = json?.details ? `\nDetalhes: ${JSON.stringify(json.details)}` : "";
    die(`Falha na requisição ${res.status} ${msg}${details}`);
  }
  return json;
}

async function getPost(postId) {
  return wixFetch(`${BASE_URL}/posts/${encodeURIComponent(postId)}`, {
    method: "GET",
  });
}

async function ensureDraft(postId) {
  // Tenta criar/garantir rascunho para um post publicado.
  // Alguns ambientes podem já criar o rascunho automaticamente ao editar; este passo é idempotente.
  try {
    return await wixFetch(`${BASE_URL}/posts/${encodeURIComponent(postId)}/create-draft`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  } catch (e) {
    // Se o endpoint não existir/404, assume que já há rascunho utilizável
    console.warn("Aviso: create-draft indisponível; prosseguindo com atualização direta do rascunho.");
    return null;
  }
}

async function updatePost(postId, payload) {
  return wixFetch(`${BASE_URL}/posts/${encodeURIComponent(postId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

async function publishPost(postId) {
  return wixFetch(`${BASE_URL}/posts/${encodeURIComponent(postId)}/publish`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

function pickUpdatePayload(localJson, currentPost) {
  // Define quais campos vamos atualizar. Mantemos a revision atual no payload.
  const allowed = [
    "title",
    "excerpt",
    "slug",
    "featured",
    "pinned",
    "categoryIds",
    "coverMedia",
    "hashtags",
    "minutesToRead",
    "tagIds",
    "language",
    "media",
    "richContent",
  ];
  const payload = { id: currentPost?.post?.id || currentPost?.id, revision: (currentPost?.post?.revision ?? currentPost?.revision) };
  for (const k of allowed) {
    if (k in localJson) payload[k] = localJson[k];
  }
  return payload;
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help || !args.postId || !args.file) {
    console.log(usage());
    process.exit(0);
  }

  const filePath = path.resolve(args.file);
  if (!fs.existsSync(filePath)) die(`Arquivo não encontrado: ${filePath}`);
  const localJson = JSON.parse(fs.readFileSync(filePath, "utf8"));

  console.log("➡️  Buscando post atual no Wix...");
  const current = await getPost(args.postId);
  const post = current.post || current; // compat
  if (!post?.id) die("Resposta inesperada ao buscar post (sem id).");
  console.log(`✔️  Post localizado: ${post.id} | status: ${post.status || post.state || "(desconhecido)"}`);

  // Se publicado, garantir rascunho antes de atualizar
  const isPublished = (post.status === "PUBLISHED" || post.published === true);
  if (isPublished) {
    console.log("➡️  Post está publicado. Garantindo rascunho para edição...");
    await ensureDraft(post.id);
    console.log("✔️  Rascunho pronto.");
  }

  // Atualização com controle de revision
  const payload = pickUpdatePayload(localJson, current);
  if (!payload.revision && post.revision) payload.revision = post.revision;
  if (!payload.revision) console.warn("⚠️  Revision ausente. A API pode recusar por concorrência.");

  console.log("➡️  Enviando atualização do rascunho...");
  const updated = await updatePost(post.id, payload);
  const newRev = updated?.post?.revision ?? updated?.revision;
  console.log(`✔️  Atualizado. Nova revision: ${newRev ?? "(indisponível)"}`);

  if (args.publish) {
    console.log("➡️  Publicando rascunho atualizado...");
    await publishPost(post.id);
    console.log("✔️  Publicado com sucesso.");
  } else {
    console.log("ℹ️  Atualização feita no rascunho. Use --publish para publicar.");
  }
}

main().catch((err) => {
  const m = err?.message || String(err);
  console.error("Erro:", m);
  process.exit(1);
});

