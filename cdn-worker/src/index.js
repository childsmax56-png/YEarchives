export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Debug endpoint — lists first 20 objects in the bucket
    if (url.pathname === '/debug-list') {
      const listed = await env.COVERS.list({ limit: 20 });
      const keys = listed.objects.map(o => o.key);
      return new Response(JSON.stringify(keys, null, 2), {
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
      });
    }

    // Strip leading slash and decode the path
    const key = decodeURIComponent(url.pathname.slice(1));

    if (!key) {
      return new Response('Not found', { status: 404 });
    }

    // Try the key as-is first, then common image extensions
    const candidates = [key, `${key}.jpg`, `${key}.jpeg`, `${key}.png`, `${key}.webp`];

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

    return new Response(`Not found: ${key}`, { status: 404 });
  }
};
