export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Debug: list first 20 keys
    if (url.pathname === '/debug-list') {
      const listed = await env.COVERS.list({ limit: 20 });
      const keys = listed.objects.map(o => o.key);
      return new Response(JSON.stringify(keys, null, 2), {
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
      });
    }

    // Debug: test fetching a known object directly
    if (url.pathname === '/debug-fetch') {
      const testKey = 'Before The College Dropout/World Record Holders.jpg';
      const obj = await env.COVERS.get(testKey);
      return new Response(obj ? `SUCCESS: found "${testKey}"` : `FAIL: not found "${testKey}"`, {
        headers: { 'Access-Control-Allow-Origin': '*' }
      });
    }

    // Build the R2 key from the URL path
    // Path format: /{era}/{name}  — both segments URL-encoded
    const parts = url.pathname.slice(1).split('/');
    if (parts.length < 2) {
      return new Response('Invalid path', { status: 400 });
    }
    const era  = decodeURIComponent(parts[0]);
    const name = decodeURIComponent(parts.slice(1).join('/'));
    const base = `${era}/${name}`;

    // Try with common image extensions
    const candidates = [base, `${base}.jpg`, `${base}.jpeg`, `${base}.png`, `${base}.webp`];

    for (const candidate of candidates) {
      const object = await env.COVERS.get(candidate);
      if (object) {
        const headers = new Headers();
        object.writeHttpMetadata(headers);
        headers.set('etag', object.httpEtag);
        headers.set('Cache-Control', 'public, max-age=31536000, immutable');
        headers.set('Access-Control-Allow-Origin', '*');
        return new Response(object.body, { headers });
      }
    }

    return new Response(`Not found: "${base}" (tried ${candidates.length} variants)`, { status: 404 });
  }
};
