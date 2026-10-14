The daily usage report for our customers in other time zones is off. Twice a year, around when the clocks change, the per-day numbers stop matching what customers count in their own dashboards. Some events land on the wrong date for a few weeks.

The report is built by `daily_counts` in `/app/rollup/daily.py`. It gets event timestamps (timezone-aware UTC datetimes) and the customer's IANA time zone name, e.g. `America/New_York`, and should return the number of events for each calendar date in that customer's local time. The CLI wrapper (`python -m rollup <tz> < timestamps.txt`) prints the same thing as `YYYY-MM-DD,count` lines in date order. Please keep that output format.

Can you fix it so each event is counted on the local date it actually happened?
