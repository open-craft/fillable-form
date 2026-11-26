const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');

const outputDir = path.resolve(__dirname, '..', 'static');

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
    optimization: {
      minimizer: [new TerserPlugin({ extractComments: false })],
    },
    resolve: { extensions: ['.tsx', '.ts', '.js', '.jsx'] },
    module: {
      rules: [
        tsRule,
        // Imported as a string and injected into the shadow DOM by createXBlockRoot.
        { test: /\.css$/, use: [{ loader: 'css-loader', options: { url: false, exportType: 'string' } }] },
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
    optimization: {
      minimizer: [new TerserPlugin({ extractComments: false })],
    },
    resolve: { extensions: ['.tsx', '.ts', '.js', '.jsx'] },
    module: {
      rules: [
        tsRule,
        // Imported as a string and injected into the shadow DOM by createXBlockRoot.
        { test: /\.css$/, use: [{ loader: 'css-loader', options: { url: false, exportType: 'string' } }] },
        ...paragonAssetRules,
      ],
    },
  },
];
