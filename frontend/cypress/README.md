# E2E Testing Suite for Task Manager

This directory contains comprehensive end-to-end tests for the Task Manager React frontend using Cypress.

## 📁 Test Structure

```
cypress/
├── e2e/                    # Test specifications
│   ├── auth.cy.js         # Authentication flows
│   ├── tasks.cy.js        # Task management workflows  
│   ├── realtime.cy.js     # WebSocket real-time updates
│   └── quotes.cy.js       # External quote feature
├── fixtures/              # Test data
│   ├── test-data.json     # Sample data and API responses
│   └── test-document.txt  # File for attachment testing
├── support/               # Configuration and utilities
│   ├── commands.js        # Custom Cypress commands
│   └── e2e.js            # Global configuration
├── scripts/              # Test automation scripts
│   └── run-e2e-tests.js  # Test runner with setup/teardown
└── cypress.config.js     # Cypress configuration
```

## 🧪 Test Coverage

### Authentication Tests (`auth.cy.js`)
- ✅ Login form validation and error handling
- ✅ Successful login with user and admin credentials  
- ✅ Logout functionality and session cleanup
- ✅ Session persistence on page refresh
- ✅ Route protection for authenticated/unauthenticated users
- ✅ Token expiration and automatic logout

### Task Workflow Tests (`tasks.cy.js`)
- ✅ Task creation with validation
- ✅ Task editing and updates
- ✅ Task status management (todo, in-progress, done)
- ✅ Task deletion with confirmation
- ✅ File attachment upload/delete
- ✅ Error handling for API failures
- ✅ Form validation and user feedback

### Real-time Update Tests (`realtime.cy.js`)
- ✅ WebSocket connection establishment
- ✅ Real-time task creation notifications
- ✅ Real-time task updates and status changes
- ✅ Real-time task deletion
- ✅ Admin monitoring of all user activities
- ✅ Attachment updates via WebSocket
- ✅ Connection error handling and reconnection
- ✅ Performance with multiple rapid updates

### External Quote Tests (`quotes.cy.js`)
- ✅ Quote fetching and display on page load
- ✅ Quote refresh functionality
- ✅ Loading states and error handling
- ✅ Network error and timeout handling
- ✅ Quote caching and persistence
- ✅ Category filtering (if supported)
- ✅ Accessibility compliance
- ✅ Integration with task workflows

## 🚀 Quick Start

### Prerequisites
- Node.js and npm installed
- Frontend and backend services available
- Cypress installed (`npm install`)

### Running Tests

#### Interactive Mode (Development)
```bash
# Open Cypress Test Runner
npm run cypress:open

# Or use the custom script
node cypress/scripts/run-e2e-tests.js --open
```

#### Headless Mode (CI/CD)
```bash
# Run all tests headlessly
npm run cypress:run

# Run with specific browser
npm run cypress:run:chrome
npm run cypress:run:firefox

# Use custom script with setup/teardown
node cypress/scripts/run-e2e-tests.js
```

#### Skip Service Setup
```bash
# If services are already running
node cypress/scripts/run-e2e-tests.js --skip-setup
```

## ⚙️ Configuration

### Environment Variables (`cypress.config.js`)
```javascript
env: {
  apiUrl: 'http://localhost:8000/api',
  testUser: {
    username: 'testuser',
    email: 'test@example.com', 
    password: 'testpass123'
  },
  testAdmin: {
    username: 'admin',
    email: 'admin@example.com',
    password: 'admin123'
  }
}
```

### Test Data (`fixtures/test-data.json`)
Contains sample tasks, users, API responses, and test attachments for consistent testing.

## 🎯 Custom Commands

The test suite includes custom Cypress commands for common operations:

### Authentication
```javascript
cy.login(username, password)       // Login with credentials
cy.loginAsUser()                   // Quick user login
cy.loginAsAdmin()                  // Quick admin login  
cy.logout()                        // Logout and verify
```

### Task Management
```javascript
cy.createTask(title, description, priority)  // Create new task
cy.editTask(taskTitle, newTitle, newDesc)    // Edit existing task
cy.deleteTask(taskTitle)                     // Delete task with confirmation
cy.changeTaskStatus(taskTitle, newStatus)    // Update task status
```

### Attachments
```javascript
cy.uploadAttachment(taskTitle, fileName)     // Upload file to task
cy.verifyTaskCount(expectedCount)            // Verify task list count
```

### Real-time Testing
```javascript
cy.waitForTaskUpdate(taskTitle)              // Wait for WebSocket update
cy.verifyToastMessage(message)               // Check notification
```

### Quote Feature
```javascript
cy.checkQuoteDisplay()                       // Verify quote section
```

## 📊 Test Reports

Tests generate reports in multiple formats:

- **Videos**: `cypress/videos/` - Test execution recordings
- **Screenshots**: `cypress/screenshots/` - Failure screenshots  
- **JSON Reports**: `cypress/reports/` - Detailed test results
- **Console Output**: Real-time test progress and results

## 🔧 Best Practices

### Data-cy Attributes
Tests use `data-cy` attributes for reliable element selection:
```html
<button data-cy="create-task-button">Create Task</button>
<div data-cy="task-card">Task content</div>
<input data-cy="task-title-input" />
```

### Test Isolation
- Each test starts with a clean state (localStorage/cookies cleared)
- API calls are intercepted and mocked for consistency
- Test data is cleaned up after each run

### Error Handling
- Network errors are simulated and tested
- API failures are mocked and verified
- Graceful degradation is validated

### Performance
- Tests include timeouts for async operations
- Real-time updates are tested with realistic delays
- Multiple concurrent operations are verified

## 🐛 Debugging

### Common Issues

**Tests failing to find elements:**
- Verify `data-cy` attributes exist in components
- Check for dynamic content loading
- Increase timeouts for slow operations

**API mocking not working:**
- Verify intercept patterns match actual endpoints
- Check request/response formats
- Ensure aliases (`@requestName`) are correct

**WebSocket tests failing:**
- Verify WebSocket connection is established
- Check event handling in application
- Ensure proper cleanup between tests

### Debug Mode
```bash
# Run with browser visible
npm run cypress:run:headed

# Enable debug logging
DEBUG=cypress:* npm run cypress:run
```

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Node
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm install
      - name: Run E2E tests
        run: node cypress/scripts/run-e2e-tests.js
      - name: Upload test results
        uses: actions/upload-artifact@v2
        if: always()
        with:
          name: cypress-results
          path: cypress/reports/
```

## 📈 Extending Tests

### Adding New Test Cases
1. Create new `.cy.js` file in `cypress/e2e/`
2. Follow existing patterns for setup/teardown
3. Use custom commands for common operations
4. Add appropriate `data-cy` attributes to components
5. Update test data fixtures if needed

### Adding Custom Commands
1. Add to `cypress/support/commands.js`
2. Follow naming convention: `cy.actionSubject()`
3. Include error handling and assertions
4. Document usage in this README

## 🎖️ Test Quality Metrics

- **Coverage**: Tests cover all major user workflows
- **Reliability**: Tests are deterministic and stable
- **Maintainability**: Tests use reusable commands and patterns
- **Performance**: Tests complete in reasonable time
- **Documentation**: All tests are well-documented

## 📝 Notes

- Tests assume clean database state between runs
- File uploads use fixtures from `cypress/fixtures/`
- WebSocket tests simulate real-time scenarios
- Admin tests verify role-based access control
- Error scenarios are thoroughly tested