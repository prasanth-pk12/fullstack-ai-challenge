/// <reference types="cypress" />

describe('Quote Feature Tests', () => {
  beforeEach(() => {
    cy.clearLocalStorage()
    cy.clearCookies()
    
    // Set up authentication
    const validToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsInVzZXJfaWQiOjEsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNzA1MzI5NjAwfQ.fake-signature'
    cy.window().then((win) => {
      win.localStorage.setItem('auth_token', validToken)
    })
    
    // Mock tasks API
    cy.intercept('GET', '**/tasks/**', { statusCode: 200, body: [] }).as('getTasks')
  })

  it('should display external quote', () => {
    // Mock quote API with correct response format
    cy.intercept('GET', '**/external/quote?use_fallback=true', {
      statusCode: 200,
      body: {
        content: "The only way to do great work is to love what you do.",
        author: "Steve Jobs",
        tags: ["motivational", "work"],
        length: 52,
        source: "quotable.io"
      }
    }).as('getQuote')
    
    cy.visit('/tasks')
    cy.wait('@getTasks')
    cy.wait('@getQuote')
    
    // Should display quote content and author
    cy.contains('Steve Jobs').should('be.visible')
    cy.contains('The only way to do great work').should('be.visible')
  })

  it('should handle quote API errors', () => {
    // Mock quote API error (intercept both with and without query params)
    cy.intercept('GET', '**/external/quote*', {
      statusCode: 500,
      body: { error: 'Service unavailable' }
    }).as('getQuoteError')
    
    cy.visit('/tasks')
    cy.wait('@getTasks')
    
    // Page should still load even if quote fails
    cy.contains('Tasks').should('be.visible')
  })
})