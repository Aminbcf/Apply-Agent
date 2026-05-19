import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

/**
 * Sample test for the App component.
 * Install @testing-library/react and @testing-library/jsdom as needed.
 */
describe('App Component', () => {
  it('should render without crashing', () => {
    render(<App />);
    expect(document.body).toBeTruthy();
  });
});
