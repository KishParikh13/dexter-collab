#!/usr/bin/env node
/**
 * Calendar Server
 * Serves Google Calendar events via HTTP API using gcal.py
 * 
 * Usage: node calendar-server.js [port]
 * Default port: 3849
 */

const http = require('http');
const { spawn } = require('child_process');
const path = require('path');

const PORT = parseInt(process.argv[2]) || 3849;
const GCAL_SCRIPT = '/data/workspace/skills/google-calendar/gcal.py';

// Calendar IDs to fetch
const CALENDARS = {
  'Work': 'kishparikh18@gmail.com',
  'Personal': '125rsiih89gregb0ffera4rfs8@group.calendar.google.com',
  'Projects': 'f2tsja9r7ad5feu73gh9t5ai5s@group.calendar.google.com',
  'Volunteering': 'covpast5nonv2t1pq2ep489fq8@group.calendar.google.com',
  'Finances': '0da3b46006b64e70483b830ba5b187063ae054d1e54346f22de5fa9ae9456dd8@group.calendar.google.com'
};

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Content-Type': 'application/json'
};

function respond(res, statusCode, data) {
  res.writeHead(statusCode, corsHeaders);
  res.end(JSON.stringify(data));
}

// Fetch events from a single calendar using Python
function fetchCalendarEvents(calendarName, calendarId, days = 7) {
  return new Promise((resolve, reject) => {
    const pythonCode = `
import json
import sys
sys.path.insert(0, '/data/workspace/skills/google-calendar')
from gcal import get_service
from datetime import datetime, timedelta, timezone

try:
    service = get_service()
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=${days})
    
    events_result = service.events().list(
        calendarId='${calendarId}',
        timeMin=now.isoformat(),
        timeMax=end.isoformat(),
        maxResults=100,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    result = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end_time = event['end'].get('dateTime', event['end'].get('date'))
        
        result.append({
            'id': event['id'],
            'title': event['summary'],
            'start': start,
            'end': end_time,
            'allDay': 'T' not in start,
            'location': event.get('location'),
            'description': event.get('description'),
            'calendar': '${calendarName}',
            'htmlLink': event.get('htmlLink')
        })
    
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({'error': str(e)}), file=sys.stderr)
    sys.exit(1)
`;

    const python = spawn('python3', ['-c', pythonCode]);
    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    python.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    python.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(stderr || `Python exited with code ${code}`));
        return;
      }
      try {
        const events = JSON.parse(stdout.trim());
        resolve(events);
      } catch (e) {
        reject(new Error(`Failed to parse events: ${e.message}`));
      }
    });
  });
}

// Fetch events from all calendars
async function fetchAllEvents(days = 7) {
  const allEvents = [];
  const errors = [];

  const promises = Object.entries(CALENDARS).map(async ([name, id]) => {
    try {
      const events = await fetchCalendarEvents(name, id, days);
      allEvents.push(...events);
    } catch (e) {
      errors.push({ calendar: name, error: e.message });
      console.error(`Error fetching ${name}:`, e.message);
    }
  });

  await Promise.all(promises);

  // Sort all events by start time
  allEvents.sort((a, b) => new Date(a.start) - new Date(b.start));

  return { events: allEvents, errors };
}

// Group events by date
function groupByDate(events) {
  const grouped = {};
  
  for (const event of events) {
    // Extract date (YYYY-MM-DD) from start
    const dateStr = event.start.slice(0, 10);
    
    if (!grouped[dateStr]) {
      grouped[dateStr] = [];
    }
    grouped[dateStr].push(event);
  }
  
  return grouped;
}

// Request handler
const server = http.createServer(async (req, res) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, corsHeaders);
    res.end();
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host}`);
  const pathname = url.pathname;

  console.log(`${new Date().toISOString()} ${req.method} ${pathname}`);

  try {
    // Health check
    if (pathname === '/health' || pathname === '/') {
      return respond(res, 200, {
        status: 'ok',
        service: 'calendar-server',
        calendars: Object.keys(CALENDARS),
        time: new Date().toISOString()
      });
    }

    // Get events
    if (pathname === '/events') {
      const days = parseInt(url.searchParams.get('days')) || 7;
      const grouped = url.searchParams.get('grouped') === 'true';
      
      const { events, errors } = await fetchAllEvents(days);
      
      if (grouped) {
        return respond(res, 200, {
          events: groupByDate(events),
          totalCount: events.length,
          errors: errors.length > 0 ? errors : undefined,
          fetchedAt: new Date().toISOString()
        });
      }
      
      return respond(res, 200, {
        events,
        count: events.length,
        errors: errors.length > 0 ? errors : undefined,
        fetchedAt: new Date().toISOString()
      });
    }

    // Get calendars list
    if (pathname === '/calendars') {
      return respond(res, 200, {
        calendars: Object.entries(CALENDARS).map(([name, id]) => ({ name, id }))
      });
    }

    // Not found
    return respond(res, 404, { error: 'Not found' });

  } catch (e) {
    console.error('Error handling request:', e);
    return respond(res, 500, { error: e.message || 'Internal server error' });
  }
});

server.listen(PORT, () => {
  console.log(`Calendar Server running on http://localhost:${PORT}`);
  console.log(`Calendars: ${Object.keys(CALENDARS).join(', ')}`);
  console.log(`\nEndpoints:`);
  console.log(`  GET /events         - Get upcoming events (params: days=7, grouped=true)`);
  console.log(`  GET /calendars      - List configured calendars`);
  console.log(`  GET /health         - Health check`);
});
