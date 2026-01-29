#!/usr/bin/env node
/**
 * Chat History Server
 * Serves Moltbot session JSONL files via HTTP API
 * 
 * Usage: node chat-server.js [port]
 * Default port: 3847
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = parseInt(process.argv[2]) || 3847;
const SESSIONS_DIR = process.env.MOLTBOT_SESSIONS_DIR || '/data/.moltbot/agents/main/sessions';

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

// Parse a JSONL file and extract messages
function parseSessionFile(filepath) {
  try {
    const content = fs.readFileSync(filepath, 'utf-8');
    const lines = content.trim().split('\n').filter(l => l.trim());
    const entries = [];
    let sessionMeta = null;
    
    for (const line of lines) {
      try {
        const entry = JSON.parse(line);
        if (entry.type === 'session') {
          sessionMeta = entry;
        }
        entries.push(entry);
      } catch (e) {
        // Skip malformed lines
      }
    }
    
    return { sessionMeta, entries };
  } catch (e) {
    console.error(`Error parsing ${filepath}:`, e.message);
    return { sessionMeta: null, entries: [] };
  }
}

// Extract messages from entries (human and assistant messages)
function extractMessages(entries) {
  const messages = [];
  
  for (const entry of entries) {
    if (entry.type === 'message' && entry.message) {
      const msg = entry.message;
      const role = msg.role || 'unknown';
      
      // Extract text content
      let text = '';
      if (typeof msg.content === 'string') {
        text = msg.content;
      } else if (Array.isArray(msg.content)) {
        text = msg.content
          .filter(c => c.type === 'text')
          .map(c => c.text)
          .join('\n');
      }
      
      // Skip empty messages or system/internal messages
      if (!text.trim()) continue;
      if (text.includes('[message_id:') && text.length < 200 && role === 'user') continue;
      if (text.includes('✅ New session started')) continue;
      
      messages.push({
        id: entry.id,
        role: role,
        content: text.trim(),
        timestamp: entry.timestamp || msg.timestamp,
        model: msg.model,
        usage: msg.usage
      });
    }
  }
  
  return messages;
}

// Get list of all sessions with metadata
function listSessions() {
  try {
    if (!fs.existsSync(SESSIONS_DIR)) {
      return [];
    }
    
    const files = fs.readdirSync(SESSIONS_DIR)
      .filter(f => f.endsWith('.jsonl') && !f.includes('.lock') && !f.includes('.deleted'));
    
    const sessions = [];
    
    for (const file of files) {
      const filepath = path.join(SESSIONS_DIR, file);
      const stat = fs.statSync(filepath);
      const { sessionMeta, entries } = parseSessionFile(filepath);
      const messages = extractMessages(entries);
      
      // Get first user message as preview
      const firstUserMsg = messages.find(m => m.role === 'user');
      const preview = firstUserMsg ? firstUserMsg.content.slice(0, 100) : '';
      
      // Count actual conversation messages
      const messageCount = messages.filter(m => m.role === 'user' || m.role === 'assistant').length;
      
      sessions.push({
        id: file.replace('.jsonl', ''),
        filename: file,
        createdAt: sessionMeta?.timestamp || stat.birthtime.toISOString(),
        modifiedAt: stat.mtime.toISOString(),
        size: stat.size,
        messageCount: messageCount,
        preview: preview,
        cwd: sessionMeta?.cwd
      });
    }
    
    // Sort by modification time, newest first
    sessions.sort((a, b) => new Date(b.modifiedAt) - new Date(a.modifiedAt));
    
    return sessions;
  } catch (e) {
    console.error('Error listing sessions:', e.message);
    return [];
  }
}

// Get full session content
function getSession(sessionId) {
  const filepath = path.join(SESSIONS_DIR, `${sessionId}.jsonl`);
  
  if (!fs.existsSync(filepath)) {
    return null;
  }
  
  const { sessionMeta, entries } = parseSessionFile(filepath);
  const messages = extractMessages(entries);
  
  return {
    id: sessionId,
    meta: sessionMeta,
    messages: messages,
    totalEntries: entries.length
  };
}

// Search across all sessions
function searchSessions(query) {
  const results = [];
  const queryLower = query.toLowerCase();
  
  try {
    const files = fs.readdirSync(SESSIONS_DIR)
      .filter(f => f.endsWith('.jsonl') && !f.includes('.lock') && !f.includes('.deleted'));
    
    for (const file of files) {
      const filepath = path.join(SESSIONS_DIR, file);
      const { sessionMeta, entries } = parseSessionFile(filepath);
      const messages = extractMessages(entries);
      
      // Search through messages
      const matches = messages.filter(m => 
        m.content.toLowerCase().includes(queryLower)
      );
      
      if (matches.length > 0) {
        results.push({
          sessionId: file.replace('.jsonl', ''),
          createdAt: sessionMeta?.timestamp,
          matchCount: matches.length,
          matches: matches.slice(0, 3).map(m => ({
            role: m.role,
            preview: highlightMatch(m.content, query, 150),
            timestamp: m.timestamp
          }))
        });
      }
    }
    
    // Sort by match count
    results.sort((a, b) => b.matchCount - a.matchCount);
    
  } catch (e) {
    console.error('Error searching sessions:', e.message);
  }
  
  return results;
}

// Highlight search match in text
function highlightMatch(text, query, maxLength) {
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx === -1) return text.slice(0, maxLength);
  
  // Get context around the match
  const start = Math.max(0, idx - 50);
  const end = Math.min(text.length, idx + query.length + 100);
  let excerpt = text.slice(start, end);
  
  if (start > 0) excerpt = '...' + excerpt;
  if (end < text.length) excerpt = excerpt + '...';
  
  return excerpt;
}

// Request handler
const server = http.createServer((req, res) => {
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
        service: 'chat-history-server',
        sessionsDir: SESSIONS_DIR,
        time: new Date().toISOString()
      });
    }
    
    // List sessions
    if (pathname === '/sessions') {
      const sessions = listSessions();
      return respond(res, 200, { sessions, count: sessions.length });
    }
    
    // Get single session
    const sessionMatch = pathname.match(/^\/sessions\/([a-f0-9-]+)$/);
    if (sessionMatch) {
      const session = getSession(sessionMatch[1]);
      if (!session) {
        return respond(res, 404, { error: 'Session not found' });
      }
      return respond(res, 200, { session });
    }
    
    // Search sessions
    if (pathname === '/search') {
      const query = url.searchParams.get('q');
      if (!query) {
        return respond(res, 400, { error: 'Missing query parameter "q"' });
      }
      const results = searchSessions(query);
      return respond(res, 200, { results, query });
    }
    
    // Not found
    return respond(res, 404, { error: 'Not found' });
    
  } catch (e) {
    console.error('Error handling request:', e);
    return respond(res, 500, { error: 'Internal server error' });
  }
});

server.listen(PORT, () => {
  console.log(`Chat History Server running on http://localhost:${PORT}`);
  console.log(`Sessions directory: ${SESSIONS_DIR}`);
  console.log(`\nEndpoints:`);
  console.log(`  GET /sessions       - List all sessions`);
  console.log(`  GET /sessions/:id   - Get session details`);
  console.log(`  GET /search?q=...   - Search across sessions`);
  console.log(`  GET /health         - Health check`);
});
