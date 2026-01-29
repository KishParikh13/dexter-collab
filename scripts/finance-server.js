#!/usr/bin/env node
/**
 * Finance Server - Proxy for Lunch Money API
 * Serves financial data to the Dexter Dashboard
 * 
 * Usage: node finance-server.js [port]
 * Default port: 3848
 * 
 * Environment: LUNCHMONEY_API_KEY must be set
 */

const http = require('http');
const https = require('https');

const PORT = parseInt(process.argv[2]) || 3848;
const API_KEY = process.env.LUNCHMONEY_API_KEY;
const API_BASE = 'https://dev.lunchmoney.app/v1';

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

// Make request to Lunch Money API
function lunchMoneyRequest(endpoint) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'dev.lunchmoney.app',
      path: `/v1${endpoint}`,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(new Error('Invalid JSON response'));
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

// Format date as YYYY-MM-DD
function formatDate(date) {
  return date.toISOString().split('T')[0];
}

// Get date range for last N days
function getDateRange(days = 30) {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - days);
  return { start: formatDate(start), end: formatDate(end) };
}

// Get current month date range
function getCurrentMonthRange() {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), 1);
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  return { start: formatDate(start), end: formatDate(end) };
}

// Fetch transactions
async function getTransactions(startDate, endDate) {
  const range = startDate && endDate 
    ? { start: startDate, end: endDate }
    : getDateRange(30);
  
  const data = await lunchMoneyRequest(
    `/transactions?start_date=${range.start}&end_date=${range.end}`
  );
  
  return (data.transactions || []).map(t => ({
    id: t.id,
    date: t.date,
    payee: t.payee,
    amount: parseFloat(t.amount),
    currency: t.currency,
    category_name: t.category_name,
    category_id: t.category_id,
    notes: t.notes,
    status: t.status,
    is_income: t.is_income,
    account_name: t.asset_name || t.plaid_account_name
  }));
}

// Fetch budgets for current month
async function getBudgets() {
  const range = getCurrentMonthRange();
  const data = await lunchMoneyRequest(
    `/budgets?start_date=${range.start}&end_date=${range.end}`
  );
  
  const budgets = [];
  for (const b of data || []) {
    if (!b.data) continue;
    
    const monthKey = Object.keys(b.data)[0];
    if (!monthKey) continue;
    
    const monthData = b.data[monthKey];
    if (!monthData || !monthData.budget_amount) continue;
    
    const budgetAmount = parseFloat(monthData.budget_amount) || 0;
    const spending = parseFloat(monthData.spending_to_base) || 0;
    
    budgets.push({
      category_name: b.category_name,
      category_id: b.category_id,
      is_group: b.is_group,
      budget_amount: budgetAmount,
      spending: spending,
      remaining: budgetAmount - spending,
      percent_used: budgetAmount > 0 ? Math.round((spending / budgetAmount) * 100) : 0,
      num_transactions: monthData.num_transactions || 0
    });
  }
  
  // Sort by percent used (descending) to show most used budgets first
  budgets.sort((a, b) => b.percent_used - a.percent_used);
  
  return budgets;
}

// Fetch categories
async function getCategories() {
  const data = await lunchMoneyRequest('/categories');
  return (data.categories || []).map(c => ({
    id: c.id,
    name: c.name,
    is_income: c.is_income,
    is_group: c.is_group,
    group_id: c.group_id
  }));
}

// Calculate spending summary by category
async function getSpendingSummary(startDate, endDate) {
  const transactions = await getTransactions(startDate, endDate);
  
  const byCategory = {};
  let totalSpending = 0;
  let totalIncome = 0;
  
  for (const t of transactions) {
    const cat = t.category_name || 'Uncategorized';
    const amount = t.amount;
    
    if (!byCategory[cat]) {
      byCategory[cat] = { total: 0, count: 0 };
    }
    
    byCategory[cat].total += amount;
    byCategory[cat].count++;
    
    // Negative amounts are typically income in Lunch Money
    if (amount < 0 || t.is_income) {
      totalIncome += Math.abs(amount);
    } else {
      totalSpending += amount;
    }
  }
  
  // Convert to array and sort by spending
  const categories = Object.entries(byCategory)
    .map(([name, data]) => ({
      category: name,
      total: Math.round(data.total * 100) / 100,
      count: data.count
    }))
    .sort((a, b) => b.total - a.total);
  
  return {
    total_spending: Math.round(totalSpending * 100) / 100,
    total_income: Math.round(totalIncome * 100) / 100,
    net: Math.round((totalIncome - totalSpending) * 100) / 100,
    by_category: categories
  };
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
  
  // Check API key
  if (!API_KEY) {
    return respond(res, 500, { 
      error: 'LUNCHMONEY_API_KEY not configured',
      hint: 'Set the environment variable: export LUNCHMONEY_API_KEY="your-key"'
    });
  }
  
  try {
    // Health check
    if (pathname === '/health' || pathname === '/') {
      return respond(res, 200, { 
        status: 'ok', 
        service: 'finance-server',
        apiConfigured: !!API_KEY,
        time: new Date().toISOString()
      });
    }
    
    // Transactions (last 30 days by default)
    if (pathname === '/transactions') {
      const start = url.searchParams.get('start');
      const end = url.searchParams.get('end');
      const transactions = await getTransactions(start, end);
      return respond(res, 200, { transactions, count: transactions.length });
    }
    
    // Budgets (current month)
    if (pathname === '/budgets') {
      const budgets = await getBudgets();
      return respond(res, 200, { budgets, count: budgets.length });
    }
    
    // Categories
    if (pathname === '/categories') {
      const categories = await getCategories();
      return respond(res, 200, { categories, count: categories.length });
    }
    
    // Spending summary
    if (pathname === '/summary') {
      const start = url.searchParams.get('start');
      const end = url.searchParams.get('end');
      const summary = await getSpendingSummary(start, end);
      return respond(res, 200, { summary });
    }
    
    // All data for dashboard (combined endpoint for efficiency)
    if (pathname === '/dashboard') {
      const [transactions, budgets, summary] = await Promise.all([
        getTransactions(),
        getBudgets(),
        getSpendingSummary()
      ]);
      
      return respond(res, 200, {
        transactions: transactions.slice(0, 50), // Limit for dashboard
        budgets,
        summary,
        fetchedAt: new Date().toISOString()
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
  console.log(`Finance Server running on http://localhost:${PORT}`);
  console.log(`API Key configured: ${API_KEY ? 'Yes' : 'No'}`);
  console.log(`\nEndpoints:`);
  console.log(`  GET /dashboard      - All data for dashboard view`);
  console.log(`  GET /transactions   - Recent transactions`);
  console.log(`  GET /budgets        - Budget progress (current month)`);
  console.log(`  GET /summary        - Spending by category`);
  console.log(`  GET /categories     - All categories`);
  console.log(`  GET /health         - Health check`);
});
