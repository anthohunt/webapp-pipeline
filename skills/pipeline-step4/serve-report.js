#!/usr/bin/env node
/**
 * serve-report.js — serves a delivery report with live feedback persistence.
 *
 * Usage: node serve-report.js --project-dir /path --milestone N [--port 5201]
 *
 * Serves the report HTML and provides a /feedback endpoint that reads/writes
 * feedback to a JSON file alongside the report. The report's JS auto-saves
 * on every flag/comment change.
 */
'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');

const args = {};
for (let i = 2; i < process.argv.length; i++) {
  if (process.argv[i].startsWith('--')) {
    const key = process.argv[i].slice(2);
    args[key] = process.argv[i + 1] && !process.argv[i + 1].startsWith('--') ? process.argv[++i] : true;
  }
}

const projectDir = args['project-dir'];
const milestone = args['milestone'];
const port = parseInt(args['port'] || '5201', 10);

if (!projectDir || !milestone) {
  console.error('Usage: node serve-report.js --project-dir /path --milestone N [--port 5201]');
  process.exit(1);
}

const reportPath = path.join(projectDir, 'docs', 'delivery', `m${milestone}-delivery-report.html`);
const feedbackPath = path.join(projectDir, 'docs', 'delivery', `m${milestone}-feedback.json`);

if (!fs.existsSync(reportPath)) {
  console.error(`Report not found: ${reportPath}`);
  process.exit(1);
}

// Initialize feedback file if it doesn't exist
if (!fs.existsSync(feedbackPath)) {
  fs.writeFileSync(feedbackPath, '{}', 'utf8');
}

const MIME = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
};

const server = http.createServer((req, res) => {
  // CORS headers for local dev
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // GET /feedback — return current feedback
  if (req.method === 'GET' && req.url === '/feedback') {
    const data = fs.readFileSync(feedbackPath, 'utf8');
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(data);
    return;
  }

  // POST /feedback — save feedback
  if (req.method === 'POST' && req.url === '/feedback') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        JSON.parse(body); // validate
        fs.writeFileSync(feedbackPath, body, 'utf8');
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end('{"ok":true}');
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end('{"error":"invalid json"}');
      }
    });
    return;
  }

  // Serve report HTML (default route)
  if (req.url === '/' || req.url === '/report') {
    const html = fs.readFileSync(reportPath, 'utf8');
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(html);
    return;
  }

  // 404
  res.writeHead(404);
  res.end('Not found');
});

server.listen(port, () => {
  console.log(`Report server running at http://localhost:${port}/`);
  console.log(`Feedback file: ${feedbackPath}`);
  console.log(`Press Ctrl+C to stop.`);
});
