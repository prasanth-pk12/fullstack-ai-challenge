#!/usr/bin/env node

/**
 * E2E Test Runner Script
 * Handles setup, execution, and teardown of Cypress tests
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const config = {
  frontendPort: 3000,
  backendPort: 8000,
  cypressTimeout: 30000,
  retries: 2
};

// Utility functions
function log(message) {
  console.log(`[E2E Runner] ${new Date().toISOString()} - ${message}`);
}

function checkPort(port) {
  try {
    const cmd = process.platform === 'win32' 
      ? `netstat -ano | findstr :${port}`
      : `lsof -ti:${port}`;
    
    execSync(cmd, { stdio: 'pipe' });
    return true;
  } catch {
    return false;
  }
}

function waitForPort(port, timeout = 30000) {
  log(`Waiting for port ${port} to be ready...`);
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    if (checkPort(port)) {
      log(`Port ${port} is ready!`);
      return true;
    }
    // Wait 1 second before checking again
    execSync('timeout 1 2>NUL || sleep 1', { stdio: 'ignore', shell: true });
  }
  
  throw new Error(`Port ${port} not ready after ${timeout}ms`);
}

function startServices() {
  log('Starting application services...');
  
  // Check if frontend is running
  if (!checkPort(config.frontendPort)) {
    log('Starting frontend...');
    const frontend = spawn('npm', ['start'], {
      cwd: process.cwd(),
      stdio: 'pipe',
      shell: true
    });
    
    // Wait for frontend to be ready
    waitForPort(config.frontendPort);
  } else {
    log('Frontend already running');
  }
  
  // Check if backend is running
  if (!checkPort(config.backendPort)) {
    log('Starting backend...');
    const backend = spawn('python', ['-m', 'uvicorn', 'app.main:app', '--reload', '--port', config.backendPort.toString()], {
      cwd: path.join(process.cwd(), '..', 'backend'),
      stdio: 'pipe',
      shell: true
    });
    
    // Wait for backend to be ready
    waitForPort(config.backendPort);
  } else {
    log('Backend already running');
  }
  
  log('All services are ready!');
}

function setupTestData() {
  log('Setting up test data...');
  
  // Create test users in database (this would typically call a backend endpoint)
  try {
    const testDataSetup = `
      curl -X POST http://localhost:${config.backendPort}/api/test/setup \\
        -H "Content-Type: application/json" \\
        -d '{
          "users": [
            {
              "username": "testuser",
              "email": "test@example.com",
              "password": "testpass123",
              "role": "user"
            },
            {
              "username": "admin",
              "email": "admin@example.com", 
              "password": "admin123",
              "role": "admin"
            }
          ]
        }'
    `;
    
    // This would only work if you have a test setup endpoint
    // execSync(testDataSetup, { stdio: 'pipe' });
    log('Test data setup would be implemented here');
  } catch (error) {
    log('Test data setup skipped (endpoint not available)');
  }
}

function runCypressTests(mode = 'run') {
  log(`Running Cypress tests in ${mode} mode...`);
  
  try {
    const command = mode === 'open' ? 'cypress:run:dev' : 'cypress:run';
    execSync(`npm run ${command}`, { 
      stdio: 'inherit',
      cwd: process.cwd()
    });
    
    log('Tests completed successfully!');
    return true;
  } catch (error) {
    log(`Tests failed with exit code: ${error.status}`);
    return false;
  }
}

function cleanupTestData() {
  log('Cleaning up test data...');
  
  try {
    // Clean up test data (this would typically call a backend endpoint)
    const cleanup = `curl -X DELETE http://localhost:${config.backendPort}/api/test/cleanup`;
    // execSync(cleanup, { stdio: 'pipe' });
    log('Test data cleanup would be implemented here');
  } catch (error) {
    log('Test data cleanup failed - manual cleanup may be required');
  }
}

function generateTestReport() {
  log('Generating test report...');
  
  const reportsDir = path.join(process.cwd(), 'cypress', 'reports');
  if (fs.existsSync(reportsDir)) {
    const files = fs.readdirSync(reportsDir);
    log(`Test reports generated in: ${reportsDir}`);
    log(`Report files: ${files.join(', ')}`);
  }
}

// Main execution
async function main() {
  const args = process.argv.slice(2);
  const mode = args.includes('--headed') || args.includes('--open') ? 'open' : 'run';
  const skipSetup = args.includes('--skip-setup');
  
  log('Starting E2E test execution...');
  
  try {
    if (!skipSetup) {
      startServices();
      setupTestData();
      
      // Wait a bit for services to fully initialize
      log('Waiting for services to initialize...');
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
    
    const success = runCypressTests(mode);
    
    if (!skipSetup) {
      cleanupTestData();
    }
    
    generateTestReport();
    
    if (success) {
      log('E2E tests completed successfully! ✅');
      process.exit(0);
    } else {
      log('E2E tests failed! ❌');
      process.exit(1);
    }
    
  } catch (error) {
    log(`Error during test execution: ${error.message}`);
    log('Attempting cleanup...');
    
    if (!skipSetup) {
      cleanupTestData();
    }
    
    process.exit(1);
  }
}

// Handle process termination
process.on('SIGINT', () => {
  log('Test execution interrupted');
  cleanupTestData();
  process.exit(1);
});

process.on('SIGTERM', () => {
  log('Test execution terminated');
  cleanupTestData();
  process.exit(1);
});

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { startServices, runCypressTests, cleanupTestData };