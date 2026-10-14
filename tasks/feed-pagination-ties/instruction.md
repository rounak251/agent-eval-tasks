Customers say the activity feed in our app is missing events. When they scroll, some items never show up, mostly during busy periods when lots of things happen at once. If they load everything in one big page, the items are all there.

The paging logic is in `/app/feed/pagination.py` (`list_events`). The API layer passes the cursor through to clients as an opaque string and sends it back unchanged, so the cursor format can change if needed.

Please fix it so that paging through the feed with any page size returns every event exactly once, newest first. Events with the same timestamp should come out in a consistent order across pages.
