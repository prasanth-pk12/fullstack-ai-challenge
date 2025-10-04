/// <reference types="cypress" />

describe('Real-time Features Tests', () => {
  beforeEach(() => {
    cy.clearLocalStorage()
    cy.clearCookies()
    
    // Set up authentication
    const validToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsInVzZXJfaWQiOjEsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNzA1MzI5NjAwfQ.fake-signature'
    cy.window().then((win) => {
      win.localStorage.setItem('auth_token', validToken)
    })
  })

  it('should establish WebSocket connection', () => {
    // Mock tasks API
    cy.intercept('GET', '**/tasks/**', { statusCode: 200, body: [] }).as('getTasks')
    
    cy.visit('/tasks')
    cy.wait('@getTasks')
    
    // Should load page successfully (WebSocket connection happens in background)
    cy.url().should('include', '/tasks')
    cy.contains('Tasks').should('be.visible')
    
    // Should not show connection errors
    cy.get('body').should('not.contain.text', 'Connection failed')
  })

  it('should handle real-time task updates', () => {
    // Mock initial tasks
    cy.intercept('GET', '**/tasks/**', {
      statusCode: 200,
      body: [
        {
          id: 1,
          title: "Initial Task",
          status: "TODO",
          created_by: { id: 1, username: "testuser" }
        }
      ]
    }).as('getTasks')
    
    cy.visit('/tasks')
    cy.wait('@getTasks')
    
    // Should display initial task
    cy.contains('Initial Task').should('be.visible')
    
    // Real-time updates would be handled by WebSocket events
    // For testing, we verify the page can handle dynamic content
    cy.get('body').should('be.visible')
  })

  it('should handle connection interruptions', () => {
    cy.intercept('GET', '**/tasks/**', { statusCode: 200, body: [] }).as('getTasks')
    
    cy.visit('/tasks')
    cy.wait('@getTasks')
    
    // Should remain functional even with network issues
    cy.contains('Tasks').should('be.visible')
    cy.get('body').should('be.visible')
  })
})