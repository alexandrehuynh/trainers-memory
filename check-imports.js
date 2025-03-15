#!/usr/bin/env node

/**
 * This script verifies all import paths in your project
 * Run with: node check-imports.js
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🔍 Checking for problematic import paths...');

// More precise patterns to check for
const problematicPatterns = [
  "from '../lib/", 
  'from "../lib/',
  "from '../../lib/", 
  'from "../../lib/',
  "from '../../../lib/", 
  'from "../../../lib/',
  "from '../../../../lib/", 
  'from "../../../../lib/'
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
  
  problematicPatterns.forEach(pattern => {
    if (content.includes(pattern)) {
      console.log(`❌ Found problematic import in ${file}: ${pattern}...`);
      // Show the line that has the problem
      const lines = content.split('\n');
      for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes(pattern)) {
          console.log(`   Line ${i+1}: ${lines[i].trim()}`);
        }
      }
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