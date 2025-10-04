/// <reference types="cypress" />

// Custom Cypress commands for Task Manager E2E tests

// Authentication commands
Cypress.Commands.add('login', (username, password) => {
  cy.visit('/login')
  cy.get('input[name="username"]').type(username)
  cy.get('input[name="password"]').type(password)
  cy.get('button[type="submit"]').click()
  cy.wait('@loginRequest')
  cy.url().should('include', '/tasks')
})

Cypress.Commands.add('loginAsUser', () => {
  const { username, password } = Cypress.env('testUser')
  cy.login(username, password)
})

Cypress.Commands.add('loginAsAdmin', () => {
  const { username, password } = Cypress.env('testAdmin')
  cy.login(username, password)
})

Cypress.Commands.add('logout', () => {
  cy.get('[data-cy=user-menu-button]').click()
  cy.get('[data-cy=logout-button]').click()
  cy.wait('@logoutRequest')
  cy.url().should('include', '/login')
})

// Task management commands
Cypress.Commands.add('createTask', (title, description, priority = 'medium') => {
  cy.get('[data-cy=create-task-button]').click()
  cy.get('[data-cy=task-title-input]').type(title)
  if (description) {
    cy.get('[data-cy=task-description-input]').type(description)
  }
  cy.get('[data-cy=task-priority-select]').select(priority)
  cy.get('[data-cy=save-task-button]').click()
  cy.wait('@createTask')
})

Cypress.Commands.add('editTask', (taskTitle, newTitle, newDescription) => {
  cy.contains('[data-cy=task-card]', taskTitle).within(() => {
    cy.get('[data-cy=edit-task-button]').click()
  })
  cy.get('[data-cy=task-title-input]').clear().type(newTitle)
  if (newDescription) {
    cy.get('[data-cy=task-description-input]').clear().type(newDescription)
  }
  cy.get('[data-cy=save-task-button]').click()
  cy.wait('@updateTask')
})

Cypress.Commands.add('deleteTask', (taskTitle) => {
  cy.contains('[data-cy=task-card]', taskTitle).within(() => {
    cy.get('[data-cy=delete-task-button]').click()
  })
  cy.get('[data-cy=confirm-delete-button]').click()
  cy.wait('@deleteTask')
})

Cypress.Commands.add('changeTaskStatus', (taskTitle, newStatus) => {
  cy.contains('[data-cy=task-card]', taskTitle).within(() => {
    cy.get('[data-cy=task-status-badge]').click()
    cy.get(`[data-cy=status-option-${newStatus}]`).click()
  })
  cy.wait('@updateTask')
})

// Attachment commands (using native Cypress file handling)
Cypress.Commands.add('uploadAttachment', (taskTitle, fileName) => {
  cy.contains('[data-cy=task-card]', taskTitle).within(() => {
    cy.get('[data-cy=upload-attachment-button]').click()
  })
  
  const filePath = `cypress/fixtures/${fileName}`
  cy.get('input[type="file"]').selectFile(filePath)
  cy.get('[data-cy=upload-button]').click()
  cy.wait('@uploadAttachment')
})

// WebSocket and real-time commands
Cypress.Commands.add('waitForTaskUpdate', (taskTitle) => {
  cy.contains('[data-cy=task-card]', taskTitle, { timeout: 10000 }).should('be.visible')
})

Cypress.Commands.add('verifyTaskCount', (expectedCount) => {
  cy.get('[data-cy=task-card]').should('have.length', expectedCount)
})

// Quote commands
Cypress.Commands.add('checkQuoteDisplay', () => {
  cy.get('[data-cy=quote-section]').should('be.visible')
  cy.get('[data-cy=quote-text]').should('not.be.empty')
  cy.get('[data-cy=quote-author]').should('not.be.empty')
})

// Utility commands
Cypress.Commands.add('waitForPageLoad', () => {
  cy.get('[data-cy=loading-spinner]').should('not.exist')
  cy.get('body').should('be.visible')
})

Cypress.Commands.add('verifyToastMessage', (message) => {
  cy.get('[data-cy=toast]').should('contain.text', message)
})

// Database cleanup commands (for test isolation)
Cypress.Commands.add('cleanupTestData', () => {
  // This would typically call a backend endpoint to clean up test data
  cy.request({
    method: 'DELETE',
    url: `${Cypress.env('apiUrl')}/test/cleanup`,
    failOnStatusCode: false
  })
})

// Network simulation commands
Cypress.Commands.add('simulateNetworkError', () => {
  cy.intercept('GET', '**/api/tasks', { forceNetworkError: true }).as('networkError')
})

Cypress.Commands.add('simulateSlowNetwork', () => {
  cy.intercept('GET', '**/api/tasks', { delay: 5000 }).as('slowNetwork')
})