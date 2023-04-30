import time
import os
import datetime
from zoneinfo import ZoneInfo
from dateutil.rrule import rrulestr
from dateutil import tz
import pytz
# We need Assignment name, start time, end time, and "completed".
# We can assume that assignments in the calendar past the current time
# have already been completed.

# We only really ping based on start time, so we don't care too much about end time.
# However, if no end time is specified, we can make the end time "All-day"

# So we need assignment date, start time, and completion status
# Calendar files don't keep track of "completed" status;
# This is functionality that we are adding.

# We need to iterate over each VEVENT
# and keep track of DTSTART and SUMMARY

def time_to_epoch(user_time: str, time_zone: str=None) -> int:
    """Converts the time from <user_time> to the respective epoch time.
    <user_time> is formatted based on the .ics specification, meaning it
    either contains just the date, the date + time in UTC, or the date + time
    in the user's local timezone.
    """
    colon_index = user_time.index(':') + 1

    # the T's position would be colon_index + 8
    # if there is no character there (colon_index + 8 >= len(line))
    if colon_index + 8 >= len(user_time):
        user_time = user_time[colon_index:colon_index+8]
        format = "%Y%m%d"
        return datetime.datetime.strptime(user_time, format).replace(tzinfo=datetime.timezone.utc)
    
    # By this point, we know that the time exists.
    # Next, we check if a "Z" is the last character in line.
    # This implies the time is already in UTC.

    if user_time[-1] == "Z":
        user_time = user_time[colon_index:len(user_time)-1]  # ignoring the Z
        format = "%Y%m%dT%H%M%S"
        return datetime.datetime.strptime(user_time, format).replace(tzinfo=datetime.timezone.utc)

    # If we got to this point, then this time event is using "floating time".
    # The timezone may or may not be provided in this line, so we must check if it exists.
    if "TZID" in user_time:
        # We need to locate the TZID module
        tzid_index = user_time.find("TZID=") + len("TZID=")
        tzid = user_time[tzid_index:colon_index-1]  # colon index must follow the timezone by .ics standards
        time_zone = pytz.timezone(tzid)
        user_time = user_time[colon_index:]
        format = "%Y%m%dT%H%M%S"
        user_time = time_zone.localize(datetime.datetime.strptime(user_time, format))
        # print(user_time)
        return user_time
    
    # otherwise we hope that we got the timezone earlier in the .ics format
    if time_zone:
        time_zone = pytz.timezone(time_zone)
        user_time = user_time[colon_index:]
        format = "%Y%m%dT%H%M%S"
        return time_zone.localize(datetime.datetime.strptime(user_time, format))

    # by this point we do not have a timezone.
    # therefore this is a floating point time, and is not bound to a timezone.
    # we should therefore automatically convert it to UTC, as a protocol.
    user_time = user_time[colon_index:]
    format = "%Y%m%dT%H%M%S"
    return datetime.datetime.strptime(user_time, format).replace(tzinfo=datetime.timezone.utc)

def get_dst(dt, timezone):
    # print(timezone)
    dt = dt.replace(tzinfo=None)
    timezone = pytz.timezone(timezone)
    d_aware = timezone.localize(dt)
    # dt = dt.replace(tzinfo=timezone)
    if d_aware.dst().seconds == 0:
        return datetime.timedelta(seconds=0)
    else:
        return datetime.timedelta(seconds=3600)
    # timezone_aware_date = timezone.localize(dt, is_dst=None)
    # return timezone_aware_date.tzinfo._dst.seconds != 0

def parse_ics(path: str) -> dict | str:
    """Parse the .ics file indicated by <path>.
    """
    try:
        events = []
        os.environ['TZ'] = 'UTC'  # for time-related purposes
        time_zone = "-1"
        with open(path, "r") as file:
            curr_event = {}
            for line in file:
                line = line.strip().replace('\\', '')  # also replacing '\' character
                # End of the event
                if line == "END:VEVENT":

                    # we should check if the assignment has a name
                    # if not, we need a default naming convention
                    # I'm thinking "Assignment #i" if this is the i'th assignment.
                    if "Name" not in curr_event:
                        curr_event["Name"] = f"Assignment {len(events)}"

                    # If the event repeats (we need to add the same event multiple times)
                    if "Repeating" in curr_event:
                        # Get the start date
                        start_time = curr_event["Start time"]
                        if "End time" in curr_event:
                            end_time = curr_event["End time"]
                        else:
                            end_time = start_time
                        duration = end_time - start_time
                        # i need to trim the curr_event["Repeating"]
                        rules_index = curr_event["Repeating"].index("RRULE:") + len("RRULE:")
                        rule = curr_event["Repeating"][rules_index:]
                        rule = rrulestr(rule, dtstart=start_time.astimezone(pytz.utc))
                        for time in list(rule):  # all the times of the event
                            new_event = curr_event.copy()
                            new_event.pop("Repeating")
                            new_event["Start time"] = datetime.datetime.timestamp(time - get_dst(time, start_time.tzinfo.zone))
                            new_event["End time"] = datetime.datetime.timestamp(time + duration - get_dst(time, start_time.tzinfo.zone))
                            events.append(new_event)
                    
                        curr_event.pop("Repeating")
                    curr_event["Start time"] = datetime.datetime.timestamp(curr_event["Start time"])
                    if "End time" in curr_event:
                        curr_event["End time"] = datetime.datetime.timestamp(curr_event["End time"])
                    events.append(curr_event)
                # Start of the event
                elif line == "BEGIN:VEVENT":
                    curr_event = {}
                # Checking if a timezone is provided
                elif "TIMEZONE" in line:
                    if time_zone != "-1":
                        continue
                    colon_index = line.find(':') + 1
                    time_zone = line[colon_index:]

                # Time (start or end, will be specified in a later line.)
                elif line.startswith("DTSTART") or line.startswith("DTEND"):
                    # DTSTART is either DATE or DATE-TIME
                    # DATE: YYYYMMDD
                    # DATE-TIME: YYYYMMDD<T>HHMMSS
                    # where the "T" separates the DATE and the TIME.

                    # DATE-TIME may or may not end with a "Z".
                    # "Z" signifies that the date is in UTC.
                    # A lack of "Z" signifies local time, which may or may
                    # not be specified in the line.

                    # We are guaranteed that after the colon (:) in DSTART
                    # is AT LEAST the date, in the specified format.

                    # After a "T" (if it is present) is a time,
                    # which may or may not end with a "Z".
                    if time_zone != "-1":
                        user_time = time_to_epoch(line.strip(), time_zone)
                    else:
                        user_time = time_to_epoch(line.strip())

                    # Specifying if this is a start time or end time
                    start_or_end = "Start time" if line.startswith("DTSTART") else "End time"
                    curr_event[start_or_end] = user_time

                elif line.startswith("SUMMARY"):
                    colon_index = line.find(':') + 1
                    curr_event["Name"] = line[colon_index:]
                    continue

                # we also need to parse "RRULE", or a recurring event.
                elif line.startswith("RRULE"):
                    # this could be used for things other than events, so I want to check if
                    # the curr_event dict is empty.
                    # This implies that an event hasn't started yet.
                    # (RRULE lines always follow a DTSTART and DTEND line, if the DTEND exists.)

                    curr_event["Repeating"] = line

            return events
    # In case anything goes wrong.
    except Exception as e:
        return -1


if __name__ == "__main__":
    db = parse_ics("test4.ics")
    print(db)