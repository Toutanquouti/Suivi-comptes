/* Carnet de comptes : fonctionnement hors connexion.
   L'appli s'ouvre depuis le cache (instantané, même sans réseau) et se met à jour en arrière-plan.
   Une nouvelle version publiée sur GitHub apparaît donc au lancement suivant. */
const CACHE = 'carnet-v1';
const POLICES = 'carnet-polices';
const FICHIERS = ['./index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-maskable.png', './apple-touch-icon.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FICHIERS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(cles => Promise.all(cles.filter(k => k.startsWith('carnet-') && k !== CACHE && k !== POLICES).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Pages : réponse immédiate depuis le cache, mise à jour en arrière-plan
  if (req.mode === 'navigate' && url.origin === self.location.origin) {
    const reseau = fetch(req);
    e.waitUntil(reseau.then(r => {
      if (!r.ok) return;
      const copie = r.clone();
      return caches.open(CACHE).then(c => c.put('./index.html', copie));
    }).catch(() => {}));
    e.respondWith(caches.match('./index.html').then(enCache => enCache || reseau));
    return;
  }

  // Fichiers de l'appli (icônes, manifeste) : cache d'abord
  if (url.origin === self.location.origin) {
    e.respondWith(caches.match(req, {ignoreSearch: true}).then(enCache => enCache || fetch(req).then(r => {
      if (r.ok) { const copie = r.clone(); caches.open(CACHE).then(c => c.put(req, copie)); }
      return r;
    })));
    return;
  }

  // Polices Google : gardées en cache pour l'usage hors connexion
  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    e.respondWith(caches.open(POLICES).then(c => c.match(req).then(enCache => {
      const reseau = fetch(req).then(r => {
        if (r.ok || r.type === 'opaque') c.put(req, r.clone());
        return r;
      }).catch(() => enCache);
      return enCache || reseau;
    })));
  }
});
