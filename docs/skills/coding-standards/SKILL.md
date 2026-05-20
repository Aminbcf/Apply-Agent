---
name: coding-standards
description: Core coding standards for the project, enforcing code quality, readability, maintainability, and tests coverage >= 80%.
---

Code Quality Standards

This document defines the mandatory code quality standards for the project.
All contributors must follow these rules to ensure high maintainability, readability, reliability, and long-term scalability.

The project quality gate is based on principles inspired by SonarQube standards.

Quality Gates

Every pull request and merge request must satisfy the following conditions:

Metric	Required Value
Test Coverage	≥ 80%
Code Duplication	≤ 3%
Critical Bugs	0
Blocker Issues	0
Security Vulnerabilities	0
Maintainability Rating	A
Reliability Rating	A
Security Rating	A
Code Smells	Minimized
Lint Errors	0
Core Engineering Principles
1. Readability First

Code must be easy to understand without excessive explanations.

Rules
Use meaningful variable and function names.
Avoid abbreviations unless universally known.
Keep logic simple and explicit.
Prefer clarity over cleverness.
Good
const totalPrice = calculateOrderTotal(items);
Bad
const tp = calc(items);
Function Standards
Maximum Function Size

Functions should remain small and focused.

Rules
Maximum: 15–20 lines per function
One responsibility per function
Avoid deeply nested logic
Prefer early returns
Good
function validateUser(user: User): boolean {
  if (!user.email) return false;
  if (!user.password) return false;

  return true;
}
Component Standards
React Component Rules
Rules
One component = one responsibility
Split large components into smaller reusable components
Avoid business logic inside UI components
Prefer composition over inheritance
Props Must Be Read-Only

React props must always use readonly typing.

This prevents accidental mutation and improves maintainability.

Sonar Rule

typescript:S6759

Software Quality Impacted
Maintainability
Severity
Low
Good
type Props = Readonly<{
  title: string;
  count: number;
}>;

function Card(props: Props) {
  return <div>{props.title}</div>;
}
Bad
type Props = {
  title: string;
  count: number;
};
Consistency Standards
Naming Consistency
Rules
Use consistent naming conventions across the codebase
Components: PascalCase
Variables/functions: camelCase
Constants: UPPER_SNAKE_CASE
Files should match exported component names
Conventional Patterns

Code must follow community conventions.

Avoid
Non-standard architecture
Custom patterns when standard solutions exist
Reinventing framework behavior
Prefer
Established best practices
Framework conventions
Predictable project structure
Maintainability Standards

Maintainability is a priority.

Rules
Remove dead code immediately
Avoid duplicated logic
Refactor complex conditions
Keep modules decoupled
Prefer reusable utilities
Avoid massive files
File Size Limits
Type	Recommended Limit
Component	≤ 200 lines
Service	≤ 300 lines
Utility	≤ 150 lines

Large files must be refactored.

Duplication Rules
Maximum Allowed Duplication: 3%

Duplicated code increases maintenance cost and bug risk.

Rules
Extract reusable logic
Use shared utilities/hooks/services
Avoid copy-paste implementations
Refactor repeated conditions
Testing Standards
Minimum Coverage: 80%

All critical business logic must be tested.

Required Tests
Unit tests
Integration tests
Error handling tests
Edge case validation
Recommended
Component testing
API contract testing
E2E tests for critical flows
TypeScript Standards
Strict Typing Required
Rules
Avoid any
Prefer explicit types
Use union types when relevant
Use readonly whenever possible
Enable strict mode
Good
function getUser(id: string): Promise<User> {
  return api.get(id);
}
Bad
function getUser(id: any): any {
  return api.get(id);
}
Complexity Rules
Cyclomatic Complexity
Rules
Maximum complexity per function: 10
Split complex conditions into helper functions
Avoid deeply nested ternaries
Avoid
condition ? a : otherCondition ? b : c;
Error Handling
Rules
Never silently ignore errors
Always log meaningful errors
Use typed error handling
Avoid generic catch blocks
Good
try {
  await saveUser(user);
} catch (error) {
  logger.error("Failed to save user", error);
  throw error;
}
Security Standards
Mandatory Rules
Never expose secrets
No hardcoded credentials
Validate all external input
Sanitize user-generated content
Use environment variables for sensitive configuration
Clean Code Rules
Forbidden Practices
Do Not
Comment obvious code
Leave TODOs without tickets
Commit debugging logs
Use magic numbers
Use nested callbacks when avoidable
Avoid
console.log("debug");
Dependency Standards
Rules
Remove unused dependencies
Keep libraries updated
Avoid unnecessary packages
Prefer lightweight dependencies
Pull Request Requirements

Every PR must:

Pass lint checks
Pass tests
Respect quality gates
Have no blocker issues
Have no critical vulnerabilities
Be reviewed before merge
Linting & Static Analysis

Mandatory tools:

ESLint
Prettier
TypeScript strict mode
SonarQube analysis

Recommended:

Husky
lint-staged
CI/CD Quality Enforcement

The pipeline must automatically:

Run tests
Run lint checks
Run static analysis
Reject failing quality gates
Reject insufficient test coverage
Definition of Done

A task is considered complete only if:

Code is functional
Tests are added
Coverage remains ≥ 80%
Duplication remains ≤ 3%
No critical Sonar issues remain
Code review is approved
Documentation is updated if needed
Final Principle

Clean code is not optional.
Every line of code should improve the maintainability, reliability, and scalability of the project.