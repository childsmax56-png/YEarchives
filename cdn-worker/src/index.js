export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Strip leading slash and decode the path
    const key = decodeURIComponent(url.pathname.slice(1));

    if (!key) {
      return new Response('Not found', { status: 404 });
    }

    // Try to get the object from R2
    const object = await env.COVERS.get(key);

    if (!object) {
      return new Response('Not found', { status: 404 });
    }

    const headers = new Headers();
    object.writeHttpMetadata(headers);
    headers.set('etag', object.httpEtag);
    headers.set('Cache-Control', 'public, max-age=31536000, immutable');
    headers.set('Access-Control-Allow-Origin', '*');

    return new Response(object.body, { headers });
  }
};
