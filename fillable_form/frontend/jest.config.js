module.exports = {
  testEnvironment: 'jsdom',
  transform: { '^.+\\.tsx?$': 'ts-jest' },
  moduleNameMapper: { '\\.css$': 'identity-obj-proxy' },
  setupFilesAfterEnv: ['<rootDir>/src/tests/setup.ts'],
};
