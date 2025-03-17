module.exports = {
    extends: [
      'next/core-web-vitals',
      'eslint:recommended',
      'plugin:@typescript-eslint/recommended',
    ],
    parser: '@typescript-eslint/parser',
    plugins: ['@typescript-eslint', 'import', 'unused-imports'],
    rules: {
      'no-unused-vars': 'off', // Turn off the base rule as it can report incorrect errors
      '@typescript-eslint/no-unused-vars': ['warn', {
        'vars': 'all',
        'args': 'after-used',
        'ignoreRestSiblings': true,
        'argsIgnorePattern': '^_',
      }],
      'import/no-unused-modules': ['warn', {
        'unusedExports': true,
      }],
      'unused-imports/no-unused-imports': 'error',
      'unused-imports/no-unused-vars': [
        'warn',
        { 'vars': 'all', 'varsIgnorePattern': '^_', 'args': 'after-used', 'argsIgnorePattern': '^_' }
      ],
    },
    settings: {
      'import/resolver': {
        'typescript': {} // This helps eslint-plugin-import resolve paths correctly
      }
    }
  };