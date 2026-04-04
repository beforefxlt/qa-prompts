const tseslint = require('@typescript-eslint/eslint-plugin');
const tsparser = require('@typescript-eslint/parser');
const react = require('eslint-plugin-react');
const reactHooks = require('eslint-plugin-react-hooks');
const reactNative = require('eslint-plugin-react-native');
const prettier = require('eslint-config-prettier');

// [BUG-044 教训] 自定义规则：检测三元表达式两分支返回相同值
// 例如：confidence ? '' : '' 永远返回 ''，是 Bug
const noIdenticalTernaryBranches = {
  meta: {
    type: 'problem',
    docs: { description: 'Disallow ternary expressions with identical consequent and alternate' },
    schema: [],
    messages: {
      identical: 'Ternary expression has identical branches ({{value}}). This always returns the same value — likely a bug.',
    },
  },
  create(context) {
    return {
      ConditionalExpression(node) {
        const consequent = context.sourceCode.getText(node.consequent);
        const alternate = context.sourceCode.getText(node.alternate);
        if (consequent === alternate) {
          context.report({
            node,
            messageId: 'identical',
            data: { value: consequent },
          });
        }
      },
    };
  },
};

module.exports = [
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: { jsx: true },
      },
      globals: {
        jest: true,
        console: true,
        setTimeout: true,
        clearTimeout: true,
        setInterval: true,
        clearInterval: true,
      },
    },
    plugins: {
      '@typescript-eslint': tseslint,
      react,
      'react-hooks': reactHooks,
      'react-native': reactNative,
      'custom': { rules: { 'no-identical-ternary': noIdenticalTernaryBranches } },
    },
    rules: {
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',
      'react-native/no-inline-styles': 'off',
      '@typescript-eslint/no-explicit-any': 'warn',

      // [BUG-044 教训] 三元表达式两分支相同 = 100% Bug
      'custom/no-identical-ternary': 'error',
    },
  },
  prettier,
];
