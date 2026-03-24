// Cache buster - forces hard refresh when site is updated
(function() {
  const CACHE_VERSION = 'v' + new Date().toISOString().slice(0, 10);
  const CACHE_KEY = 'site-cache-version';

  // Check if we need to clear cache
  const storedVersion = localStorage.getItem(CACHE_KEY);

  if (storedVersion !== CACHE_VERSION) {
    // Cache version changed, clear everything
    localStorage.setItem(CACHE_KEY, CACHE_VERSION);

    // Clear all caches
    if ('caches' in window) {
      caches.keys().then(function(names) {
        names.forEach(function(name) {
          caches.delete(name);
        });
      });
    }

    // Force hard refresh
    if (performance.navigation.type !== 1) {
      window.location.reload(true);
    }
  }
})();

