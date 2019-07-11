from datetime import datetime, tzinfo
import pytz

# define a datetime in UTC
input_ts = 1562847126
now = datetime.fromtimestamp(input_ts, pytz.UTC)
print(now.isoformat())

# convert to local timezone
local_tz = pytz.timezone('Europe/Berlin')
now = now.astimezone(local_tz)
print(now.isoformat())
