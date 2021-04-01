"""Connects to Google Calendar API Freebusy resource to fetch availability for the day.
Runs computations to determine if free/busy at the current time. Sends data to my API.
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
from datetimerange import DateTimeRange
import pytz
from pytz import timezone


SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = './service.json'
calendar_id = 'ryan.jeffery.young@gmail.com'

def setup():
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    return service

def convertLocal(time):
    pst = timezone('US/Pacific')
    time_dt = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%Sz')
    time_utc = pytz.UTC.localize(time_dt)
    time_local = time_utc.astimezone(pst)
    time_formatted = time_local.strftime('%I:%M %p')    
    return time_formatted

def convertLocalUTC(time):
    pst = timezone('US/Pacific')
    time_dt = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%Sz')
    time_utc = pytz.UTC.localize(time_dt)
    time_local = time_utc.astimezone(pst)
    return time_local

def getApiResult(service, calendarId):
    # get today's date range
    d_today = datetime.date.today()
    d_tmr = d_today + datetime.timedelta(days=1)

    # create datetime object at start of data (0800 UTC)
    start = datetime.datetime(d_today.year, d_today.month, d_today.day, 8, 0, 0 )
    end = datetime.datetime(d_tmr.year, d_tmr.month, d_tmr.day, 7, 59, 0)
    # convert to ISO for google API
    start_UTC = start.isoformat() + 'Z'
    end_UTC = end.isoformat() + 'Z'

    body = {
    "timeMin": start_UTC,
    "timeMax": end_UTC,
    "items": [{"id": calendarId}]
    }

    # make API call
    freebusy = service.freebusy().query(body=body).execute()

    # return list of busy times for the day
    return freebusy['calendars'][calendarId]['busy']

def checkAvailable(service):
    # get list of todays events
    events_list = getApiResult(service, calendar_id)
    # get current time
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    # check if current time in any event
    if len(events_list) == 0:
        return True
    for event in events_list:
        start = event['start']
        end = event['end']                                               
        time_range = DateTimeRange(start, end)
    # return False if yes, else True
        if now in time_range:
            return False
    return True


def freeWhen(service):
    """Determines when next free time slot is
    Args:
        service (googleapiclient.discovery.Resource): Calendar resource provided by setup()

    Returns:
        string : Time when time slot of availability is
    """
    # get list of todays events
    events_list = getApiResult(service, calendar_id)
    # get current time
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    #store when current event ends
    curr_end = ''
    next_start = ''
    # iterate through events to find curr event, store end time
    for event in events_list:
        start = event['start']
        end = event['end']                                               
        time_range = DateTimeRange(start, end)
        # find curr event
        if now in time_range:
            curr_event = event
            # store end time
            curr_end = event['end']
            # find next event
            try:
                next_event = events_list[events_list.index(curr_event)+1]
                next_start = next_event['start']
                next_end = next_event['end']
            except: # if no event follows, return end of current event
                return convertLocal(curr_end) 
    # convert start & end to datetime objects
    next_start_dt = datetime.datetime.strptime(next_start, '%Y-%m-%dT%H:%M:%Sz')
    curr_end_dt = datetime.datetime.strptime(curr_end, '%Y-%m-%dT%H:%M:%Sz')
    # compute difference between curr end & next start
    gap = next_start_dt - curr_end_dt # gives datetime.timdelta object 
    # if > 10 min, say free at curr end
    if gap >= datetime.timedelta(minutes=10):
         return convertLocal(curr_end)
    else:
        # return end of next event
        print("gap less than 10 min")
        return convertLocal(next_end)

def busyWhen(service):
    """Determines when next busy time slot is
    Args:
        service (googleapiclient.discovery.Resource): Calendar resource provided by setup()

    Returns:
        string : Time when next busy slot begins
    """
    # get list of todays events
    events_list = getApiResult(service, calendar_id)
    # if list empty, return no next event
    if len(events_list) == 0:
        return None
    # get current time
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    # iterate through events list to find next event start
    next_start = ''
    
    for event in events_list:
        start = event['start']
        end = event['end']                                               
        time_range = DateTimeRange(start, end)
        # find when next event AFTER now is
        # create timedate object for event end & now
        end_dt = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%Sz')
        # strip the trailing decimals to properly convert
        now_stripped = now.split('.')[0] + 'Z'
        now_dt = datetime.datetime.strptime(now_stripped, '%Y-%m-%dT%H:%M:%Sz')
        # see if now past event
        if now_dt < end_dt:
            next_start = event['start']
            return convertLocal(next_start)
    # returns None if no next events 

def main():
    service = setup()
    print(checkAvailable(service))

if __name__ == '__main__':
    main()