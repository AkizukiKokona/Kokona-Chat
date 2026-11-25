/* 心夏 Chat 的 Service Worker：只干两件事——弹通知、点通知回到会话。 */

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (err) {
    data = { body: event.data ? event.data.text() : '' };
  }
  const icon = data.icon || '/static/icon.png';

  event.waitUntil((async () => {
    // 页面正开着（有焦点）就不弹，避免和界面里的红点重复
    try {
      const wins = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      const isTest = data.tag === 'kokona-test';
      if (!isTest && wins.some((w) => w.focused)) return;
    } catch (err) { /* 拿不到窗口就照常弹 */ }

    await self.registration.showNotification(data.title || '心夏 Chat', {
      body: data.body || '',
      icon,
      badge: '/static/icon.png',
      tag: data.tag || 'kokona-chat',
      renotify: true,
      data: { url: data.url || '/' },
    });
  })());
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || '/';

  event.waitUntil((async () => {
    const wins = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const win of wins) {
      if (win.url.indexOf(self.location.origin) !== 0) continue;
      try { await win.focus(); } catch (err) { /* 忽略 */ }
      try { if ('navigate' in win) await win.navigate(target); } catch (err) { /* 忽略 */ }
      return;
    }
    await self.clients.openWindow(target);
  })());
});
