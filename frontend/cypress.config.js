const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    viewportWidth: 1280,
    viewportHeight: 720,
    supportFile: 'cypress/support/e2e.js',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
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
    },
    // Timeouts
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    responseTimeout: 10000,
    // Test isolation
    testIsolation: true,
    // Video and screenshots
    video: true,
    screenshotOnRunFailure: true,
    // Browser settings
    chromeWebSecurity: false
  },
  component: {
    devServer: {
      framework: 'create-react-app',
      bundler: 'webpack',
    },
  },
})