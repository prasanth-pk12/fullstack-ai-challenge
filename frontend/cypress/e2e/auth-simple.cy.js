/// <reference types="cypress" />

describe('Authentication Tests', () => {
  beforeEach(() => {
    cy.clearLocalStorage()
    cy.clearCookies()
  })

  it('should display login form', () => {
    cy.visit('/login')
    
    // Check basic form elements
    cy.get('input[name="username"]').should('be.visible')
    cy.get('input[name="password"]').should('be.visible')
    cy.get('button[type="submit"]').should('be.visible')
    cy.contains('Sign in').should('be.visible')
  })

  it('should handle invalid login', () => {
    cy.visit('/login')
    
    // Mock failed login
    cy.intercept('POST', '**/auth/login', {
      statusCode: 401,
      body: { detail: 'Incorrect username or password' }
    }).as('loginFailed')
    
    // Fill form with invalid credentials
    cy.get('input[name="username"]').type('invaliduser')
    cy.get('input[name="password"]').type('wrongpassword')
    cy.get('button[type="submit"]').click()
    
    cy.wait('@loginFailed')
    
    // Should show error
    cy.contains('Incorrect username or password', { timeout: 5000 }).should('be.visible')
  })

  it('should handle successful login', () => {
    cy.visit('/login')
    
    // Mock successful login
    cy.intercept('POST', '**/auth/login', {
      statusCode: 200,
      body: {
        access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsInVzZXJfaWQiOjEsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNzA1MzI5NjAwfQ.fake-signature',
        token_type: 'bearer'
      }
    }).as('loginSuccess')
    
    // Mock tasks API for redirect
    cy.intercept('GET', '**/tasks/**', { statusCode: 200, body: [] }).as('getTasks')
    
    // Fill form with valid credentials
    cy.get('input[name="username"]').type('testuser')
    cy.get('input[name="password"]').type('testpass123')
    cy.get('button[type="submit"]').click()
    
    cy.wait('@loginSuccess')
    
    // Should show success message and redirect
    cy.contains('Welcome back!', { timeout: 5000 }).should('be.visible')
    cy.url({ timeout: 2000 }).should('include', '/tasks')
  })
})