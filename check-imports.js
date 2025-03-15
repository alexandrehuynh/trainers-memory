#!/usr/bin/env node

/**
 * This script verifies all import paths in your project
 * Run with: node check-imports.js
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🔍 Checking for problematic import paths...');

// Paths to search for
const pathsToCheck = [
  '../lib/authContext',
  '../../lib/authContext',
  '../lib/themeContext',
  '../../lib/themeContext',
  '../lib/tokenHelper',
  '../../lib/tokenHelper'
];

// Files to check
function findFiles(dir, extensions = ['.js', '.jsx', '.ts', '.tsx']) {
  let results = [];
  const list = fs.readdirSync(dir);
  
  list.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat && stat.isDirectory() && file !== 'node_modules' && file !== '.next') {
      results = results.concat(findFiles(filePath, extensions));
    } else {
      if (extensions.includes(path.extname(file).toLowerCase())) {
        results.push(filePath);
      }
    }
  });
  
  return results;
}

// Find all files in the src directory
const files = findFiles('./src');
let foundProblems = false;

// Check each file for problematic imports
files.forEach(file => {
  const content = fs.readFileSync(file, 'utf8');
  
  pathsToCheck.forEach(importPath => {
    if (content.includes(`from '${importPath}'`) || content.includes(`from "${importPath}"`)) {
      console.log(`❌ Found problematic import in ${file}: import from '${importPath}'`);
      foundProblems = true;
    }
  });
});

// Verify path aliases resolve correctly
console.log('\n🔍 Checking if path aliases resolve correctly...');

try {
  console.log('Running production build to test imports...');
  execSync('npm run build', { stdio: 'inherit' });
  console.log('✅ Production build successful!');
} catch (error) {
  console.error('❌ Production build failed, check errors above');
  process.exit(1);
}

if (!foundProblems) {
  console.log('✅ No problematic imports found in source files');
}

console.log('\n📋 Verification complete!'); 