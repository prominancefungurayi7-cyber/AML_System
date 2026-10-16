/* Device message notifications for open authenticated application pages. */
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const contact = event.notification.data?.contact || '';
  const target = new URL('/messages?contact=' + encodeURIComponent(contact), self.location.origin);
  event.waitUntil((async () => {
    const pages = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    const page = pages.find(client => new URL(client.url).origin === target.origin);
    if (page) {
      await page.focus();
      if ('navigate' in page) await page.navigate(target.href);
    } else {
      await self.clients.openWindow(target.href);
    }
  })());
});
