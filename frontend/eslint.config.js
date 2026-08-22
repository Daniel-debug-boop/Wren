import tsPlugin from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import reactPlugin from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import unusedImports from "eslint-plugin-unused-imports";
import tanstackQuery from "@tanstack/eslint-plugin-query";
import i18nextPlugin from "eslint-plugin-i18next";
import prettierPlugin from "eslint-plugin-prettier";
import globals from "globals";

const jsExtensions = "**/*.js";
const tsExtensions = "**/*.{ts,tsx}";

export default [
  {
    ignores: [
      "node_modules/**",
      "build/**",
      ".react-router/**",
      "*.cjs",
      "scripts/**",
      "playwright-report/**",
    ],
  },
  {
    files: [jsExtensions, tsExtensions],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
      react: reactPlugin,
      "react-hooks": reactHooks,
      "unused-imports": unusedImports,
      "@tanstack/query": tanstackQuery,
      i18next: i18nextPlugin,
      prettier: prettierPlugin,
    },
    settings: {
      react: { version: "detect" },
    },
    rules: {
      // Core correctness
      "no-console": "off",
      eqeqeq: ["error", "smart"],
      "prefer-const": "error",
      "no-var": "error",
      "object-shorthand": ["warn", "always"],
      "prefer-template": "warn",

      // TypeScript correctness
      "@typescript-eslint/no-unused-vars": "off",
      "unused-imports/no-unused-imports": "error",
      "unused-imports/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/explicit-module-boundary-types": "off",
      "@typescript-eslint/no-non-null-assertion": "warn",
      "@typescript-eslint/no-empty-function": "off",
      "@typescript-eslint/ban-ts-comment": "warn",

      // React
      "react/jsx-key": "error",
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "off",

      // TanStack Query
      "@tanstack/query/exhaustive-deps": "warn",
      "@tanstack/query/stable-query-client": "warn",

      // Formatting handled by prettier CLI; mirror violations as errors
      "prettier/prettier": ["error"],

      // i18n sweep tracked separately
      "i18next/no-literal-string": "warn",
    },
  },
  {
    files: [tsExtensions],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  {
    files: ["**/*.test.{ts,tsx,js}"],
    rules: {
      "i18next/no-literal-string": "off",
    },
  },
];
