import js from '@eslint/js';
import reactPlugin from 'eslint-plugin-react';
import tseslint from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';

export default [
  {
    ignores: ['dist/**', 'node_modules/**', 'src-tauri/**'],
  },
  js.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
      globals: {
        document: 'readonly',
        HTMLElement: 'readonly',
        Node: 'readonly',
        localStorage: 'readonly',
        navigator: 'readonly',
        window: 'readonly',
      },
    },
    plugins: {
      react: reactPlugin,
      '@typescript-eslint': tseslint,
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
    rules: {
      'no-undef': 'off',
      'no-unused-vars': 'off',
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
        },
      ],
    },
  },
];