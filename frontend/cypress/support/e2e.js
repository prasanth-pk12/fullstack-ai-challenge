/// <reference types="cypress" />

// Import commands.js using ES2015 syntax:
import './commands'
import 'cypress-file-upload'

// Alternatively you can use CommonJS syntax:
// require('./commands')

// Global test configuration
Cypress.on('uncaught:exception', (err, runnable) => {
  // Returning false here prevents Cypress from failing the test
  // This is useful for handling expected errors in the application
  if (err.message.includes('Network Error') || 
      err.message.includes('fetch') || 
      err.message.includes('WebSocket')) {
    return false
  }
  return true
})

// Setup and teardown hooks
beforeEach(() => {
  // Clear localStorage and sessionStorage before each test
  cy.clearLocalStorage()
  cy.clearCookies()
  
  // Set up interceptors for API calls
  cy.intercept('POST', '**/api/auth/login').as('loginRequest')
  cy.intercept('POST', '**/api/auth/logout').as('logoutRequest')
  cy.intercept('GET', '**/api/tasks').as('getTasks')
  cy.intercept('POST', '**/api/tasks').as('createTask')
  cy.intercept('PUT', '**/api/tasks/*').as('updateTask')
  cy.intercept('DELETE', '**/api/tasks/*').as('deleteTask')
  cy.intercept('POST', '**/api/tasks/*/upload').as('uploadAttachment')
  cy.intercept('GET', '**/api/external/quote').as('getQuote')
})

afterEach(() => {
  // Clean up after each test
  cy.clearLocalStorage()
  cy.clearCookies()
})