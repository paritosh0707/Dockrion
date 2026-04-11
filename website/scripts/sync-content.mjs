/**
 * Content sync pipeline: docs/usage/ -> src/content/docs/
 *
 * Reads the raw markdown from docs/usage/ (which has no YAML frontmatter),
 * extracts metadata, rewrites internal links, strips breadcrumb lines,
 * injects Starlight-compatible frontmatter, and writes to the Astro
 * content directory.  docs/usage/ is never modified.
 */

import { readFileSync, writeFileSync, mkdirSync, readdirSync, statSync, rmSync, existsSync } from 'fs';
import { join, dirname, basename, relative, extname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..', '..');
const DOCS_SRC = join(REPO_ROOT, 'docs', 'usage');
const CONTENT_DEST = join(__dirname, '..', 'src', 'content', 'docs');

// Mapping from source directory names to clean slug prefixes
const DIR_MAP = {
  '01-introduction': 'introduction',
  '02-the-dockfile': 'the-dockfile',
  '03-cli-reference': 'cli-reference',
  '04-the-generated-api': 'the-generated-api',
  '05-guides-and-recipes': 'guides-and-recipes',
  'appendix': 'appendix',
};

// Order for each directory (sidebar ordering)
const DIR_ORDER = {
  'introduction': 1,
  'the-dockfile': 2,
  'cli-reference': 3,
  'the-generated-api': 4,
  'guides-and-recipes': 5,
  'appendix': 6,
};

// Known file ordering within directories (based on numbering in docs)
const FILE_ORDER_MAP = {
  'what-is-dockrion': 1,
  'core-concepts': 2,
  'architecture-overview': 3,
  'quickstart': 4,
  'roadmap': 5,
  'agent': 1,
  'io-schema': 2,
  'metadata': 3,
  'build-config': 4,
  'env-substitution': 5,
  'secrets': 6,
  'observability': 7,
  'complete-example': 8,
  'core-commands': 1,
  'utility-commands': 2,
  'exit-codes': 3,
  'endpoints-reference': 1,
  'auth-callers-perspective': 2,
  'io-schema-and-swagger': 3,
  'streaming-consumption': 4,
  'installation': 1,
  'adding-auth': 2,
  'adding-policies': 3,
  'adding-streaming': 4,
  'environment-and-secrets': 5,
  'docker-build-and-deployment': 6,
  'cloud-deployment': 7,
  'invoice-copilot-walkthrough': 8,
  'troubleshooting': 9,
  'faq': 10,
  'adapters-reference': 1,
  'error-hierarchy': 2,
  'sdk-reference': 3,
  'api-key': 1,
  'jwt': 2,
  'oauth2': 3,
  'roles-and-rate-limits': 4,
  'prompt-injection': 1,
  'output-controls': 2,
  'tool-gating': 3,
  'sse': 1,
  'async-runs': 2,
  'backends': 3,
  'event-types': 4,
  'stream-context': 5,
};

function cleanDestination() {
  if (existsSync(CONTENT_DEST)) {
    rmSync(CONTENT_DEST, { recursive: true, force: true });
  }
  mkdirSync(CONTENT_DEST, { recursive: true });
}

function collectFiles(dir, base = '') {
  const results = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const rel = base ? join(base, entry) : entry;
    if (statSync(full).isDirectory()) {
      results.push(...collectFiles(full, rel));
    } else if (extname(entry) === '.md') {
      results.push({ fullPath: full, relPath: rel });
    }
  }
  return results;
}

/**
 * Map a source relative path to a destination relative path.
 * e.g. "01-introduction/what-is-dockrion.md" -> "introduction/what-is-dockrion.md"
 * e.g. "01-introduction/README.md" -> "introduction/index.md"
 */
function mapPath(relPath) {
  const parts = relPath.replace(/\\/g, '/').split('/');

  // Map numbered directory prefixes to clean names
  for (let i = 0; i < parts.length; i++) {
    if (DIR_MAP[parts[i]]) {
      parts[i] = DIR_MAP[parts[i]];
    }
  }

  // Rename README.md to index.md
  const last = parts[parts.length - 1];
  if (last.toLowerCase() === 'readme.md') {
    parts[parts.length - 1] = 'index.md';
  }

  return parts.join('/');
}

/**
 * Extract the first # H1 heading from markdown content.
 */
function extractTitle(content) {
  const match = content.match(/^#\s+(.+)$/m);
  if (match) {
    // Clean up: remove numbering like "1.1 " or "2.3 "
    return match[1].replace(/^\d+\.?\s*(\d+\.?\s*)*/, '').trim();
  }
  return 'Untitled';
}

/**
 * Extract the first real paragraph (after H1 and breadcrumb) as description.
 */
function extractDescription(content) {
  const lines = content.split('\n');
  let pastTitle = false;
  for (const line of lines) {
    const trimmed = line.trim();
    if (!pastTitle) {
      if (trimmed.startsWith('# ')) { pastTitle = true; continue; }
      continue;
    }
    // Skip breadcrumb lines
    if (trimmed.match(/^\[Home\]/)) continue;
    // Skip empty lines and horizontal rules
    if (trimmed === '' || trimmed === '---') continue;
    // Skip heading lines
    if (trimmed.startsWith('#')) break;
    // This is our description
    return trimmed.substring(0, 200).replace(/"/g, '\\"');
  }
  return '';
}

/**
 * Detect and strip breadcrumb lines like:
 *   [Home](../../README.md) > [Introduction](README.md)
 */
function stripBreadcrumbs(content) {
  return content.replace(/^\[Home\]\([^)]+\)(\s*>\s*\[[^\]]+\]\([^)]+\))*\s*$/gm, '');
}

/**
 * Rewrite relative markdown links so they work under the new directory structure.
 * Handles patterns like:
 *   [text](../../README.md)         -> [text](/introduction/)
 *   [text](README.md)               -> [text](./index.md) (handled by Starlight)
 *   [text](what-is-dockrion.md)     -> unchanged (same directory)
 *   [text](../README.md)            -> parent index
 */
function rewriteLinks(content, sourceRelPath) {
  return content.replace(
    /\[([^\]]*)\]\(([^)]+)\)/g,
    (match, text, href) => {
      // Skip external links and anchors
      if (href.startsWith('http') || href.startsWith('#') || href.startsWith('mailto:')) {
        return match;
      }

      // Skip image references
      if (href.match(/\.(png|jpg|jpeg|gif|svg|webp)$/i)) {
        return match;
      }

      // Rewrite README.md -> index links
      let newHref = href.replace(/README\.md/gi, 'index.md');

      // Rewrite numbered directory prefixes
      for (const [src, dest] of Object.entries(DIR_MAP)) {
        newHref = newHref.replace(new RegExp(src.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), dest);
      }

      return `[${text}](${newHref})`;
    }
  );
}

/**
 * Strip the first H1 heading from content (Starlight generates its own from frontmatter title).
 */
function stripFirstH1(content) {
  return content.replace(/^#\s+.+$/m, '').replace(/^\n+/, '');
}

function getOrder(relPath) {
  const mapped = mapPath(relPath).replace(/\\/g, '/');
  const filename = basename(mapped, '.md');

  // Index files get order 0
  if (filename === 'index') {
    const dir = dirname(mapped).split('/').pop();
    return DIR_ORDER[dir] !== undefined ? 0 : 0;
  }

  return FILE_ORDER_MAP[filename] !== undefined ? FILE_ORDER_MAP[filename] : 99;
}

function processFile({ fullPath, relPath }) {
  const raw = readFileSync(fullPath, 'utf-8');
  const title = extractTitle(raw);
  const description = extractDescription(raw);
  const order = getOrder(relPath);

  let content = raw;
  content = stripBreadcrumbs(content);
  content = stripFirstH1(content);
  content = rewriteLinks(content, relPath);

  // Build frontmatter
  const frontmatter = [
    '---',
    `title: "${title}"`,
  ];
  if (description) {
    frontmatter.push(`description: "${description}"`);
  }
  frontmatter.push(`sidebar:`);
  frontmatter.push(`  order: ${order}`);
  frontmatter.push('---');

  const finalContent = frontmatter.join('\n') + '\n\n' + content.trim() + '\n';

  // Write to destination
  const destPath = join(CONTENT_DEST, mapPath(relPath));
  mkdirSync(dirname(destPath), { recursive: true });
  writeFileSync(destPath, finalContent, 'utf-8');

  return mapPath(relPath);
}

// --- Main ---
console.log('Syncing docs/usage/ -> src/content/docs/');
console.log(`  Source: ${DOCS_SRC}`);
console.log(`  Dest:   ${CONTENT_DEST}`);

cleanDestination();

const files = collectFiles(DOCS_SRC);

// Skip the root README.md (it's a table-of-contents, not a docs page)
const docsFiles = files.filter(f => f.relPath !== 'README.md');

console.log(`  Found ${docsFiles.length} markdown files to process`);

const processed = docsFiles.map(processFile);
processed.forEach(p => console.log(`    -> ${p}`));
console.log(`  Done. ${processed.length} files synced.`);
