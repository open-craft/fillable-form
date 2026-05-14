const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const FixStyleOnlyEntriesPlugin = require('webpack-fix-style-only-entries');

const outputDir = path.resolve(__dirname, '..', 'static');
const postcssPlugins = [
  require('postcss-prefix-selector')({
    prefix: '.fillable-form-block',
    exclude: [/^@keyframes/, /^html/, /^:root/],
    transform: (prefix, selector) => {
      if (selector.startsWith('.fillable-form-block')) return selector;
      return `${prefix} ${selector}`;
    },
  }),
];

const learnerPostcssPlugins = [
  // No prefix for learner — XBlocks render in LMS iframes.
];

const tsRule = { test: /\.tsx?$/, use: 'ts-loader', exclude: /node_modules|src[\\/]tests/ };

const paragonAssetRules = [
  { test: /\.svg$/, type: 'asset/resource' },
  { test: /\.scss$/, use: ['style-loader', 'css-loader', 'sass-loader'] },
];

module.exports = [
  // ── Learner JS bundle ──────────────────────────────────
  {
    entry: { learner: './src/learner/index.tsx' },
    output: {
      path: path.join(outputDir, 'js'),
      filename: 'fillable_form_learner.js',
      library: { name: 'FillableFormLearner', type: 'window', export: 'renderBlock' },
    },
    resolve: { extensions: ['.tsx', '.ts', '.js', '.jsx'] },
    module: {
      rules: [
        tsRule,
        { test: /\.css$/, use: ['style-loader', { loader: 'css-loader', options: { url: false } }, { loader: 'postcss-loader', options: { postcssOptions: { plugins: learnerPostcssPlugins } } }] },
        ...paragonAssetRules,
      ],
    },
  },
  // ── Studio JS bundle ───────────────────────────────────
  {
    entry: { studio: './src/studio/index.tsx' },
    output: {
      path: path.join(outputDir, 'js'),
      filename: 'fillable_form_studio.js',
      library: { name: 'FillableFormStudio', type: 'window', export: 'renderBlock' },
    },
    resolve: { extensions: ['.tsx', '.ts', '.js', '.jsx'] },
    module: {
      rules: [
        tsRule,
        { test: /\.css$/, use: ['style-loader', { loader: 'css-loader', options: { url: false } }, { loader: 'postcss-loader', options: { postcssOptions: { plugins: postcssPlugins } } }] },
        ...paragonAssetRules,
      ],
    },
  },
  // ── Non-prefixed CSS file ──────────────────────────────
  {
    entry: { css: './src/fillable_form.css' },
    output: {
      path: path.join(outputDir, 'css'),
      filename: 'dummy.js',
    },
    plugins: [new FixStyleOnlyEntriesPlugin(), new MiniCssExtractPlugin({ filename: 'fillable_form.css' })],
    module: {
      rules: [
        { test: /\.css$/, use: [MiniCssExtractPlugin.loader, { loader: 'css-loader', options: { url: false } }] },
      ],
    },
  },
  // ── Prefixed CSS file (legacy Studio) ──────────────────
  {
    entry: { 'css-studio': './src/fillable_form.css' },
    output: {
      path: path.join(outputDir, 'css'),
      filename: 'dummy-studio.js',
    },
    plugins: [new FixStyleOnlyEntriesPlugin(), new MiniCssExtractPlugin({ filename: 'fillable_form_studio.css' })],
    module: {
      rules: [
        { test: /\.css$/, use: [MiniCssExtractPlugin.loader, { loader: 'css-loader', options: { url: false } }, { loader: 'postcss-loader', options: { postcssOptions: { plugins: postcssPlugins } } }] },
      ],
    },
  },
];
