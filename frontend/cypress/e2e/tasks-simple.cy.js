/// <reference types="cypress" />

describe('Task Management Tests', () => {
  beforeEach(() => {
    cy.clearLocalStorage()
    cy.clearCookies()
    
    // Set up authentication
    const validToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsInVzZXJfaWQiOjEsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNzA1MzI5NjAwfQ.fake-signature'
    cy.window().then((win) => {
      win.localStorage.setItem('auth_token', validToken)
    })
  })

  it('should display tasks page', () => {
    // Mock tasks API
    cy.intercept('GET', '**/tasks/**', {
      statusCode: 200,
      body: [
        {
          id: 1,
          title: "Test Task",
          description: "This is a test task",
          status: "TODO",
          priority: "medium",
          created_at: "2024-01-15T10:00:00Z",
          created_by: { id: 1, username: "testuser" },
          attachments: []
        }
      ]
    }).as('getTasks')
    
    cy.visit('/tasks')
    cy.wait('@getTasks')
    
    // Should display page elements
    cy.contains('Tasks').should('be.visible')
    cy.contains('New Task').should('be.visible')
    cy.contains('Test Task').should('be.visible')
  })

  it('should open task creation form', () => {
    cy.intercept('GET', '**/tasks/**', { statusCode: 200, body: [] }).as('getTasks')
    
    cy.visit('/tasks')
    cy.wait('@getTasks')
    
    // Click New Task button
    cy.contains('button', 'New Task').click()
    
    // Should show form elements (check for common form text)
    cy.get('body').should('contain.text', 'Title')
  })

  it('should handle task operations', () => {
    cy.intercept('GET', '**/tasks/**', {
      statusCode: 200,
      body: [{ id: 1, title: "Sample Task", status: "TODO" }]
    }).as('getTasks')
    
    cy.intercept('POST', '**/tasks', {
      statusCode: 201,
      body: { id: 2, title: "New Task", status: "TODO" }
    }).as('createTask')
    
    cy.visit('/tasks')
    cy.wait('@getTasks')
    
    // Should handle basic task operations
    cy.contains('Sample Task').should('be.visible')
  })
})