# Deployment Guide

## Frontend (Vercel)

### Troubleshooting Common Issues

1. **Module Resolution Issues**
   - If you see `Cannot find module '@/lib/authContext'` errors, check:
     - Ensure babel-plugin-module-resolver is in both dependencies and devDependencies
     - Verify .babelrc or .babelrc.js configuration has correct aliases
     - Use the vercel-build.sh script which explicitly installs the module resolver

2. **Build Failures**
   - If you see missing routes-manifest.json errors:
     - The build is failing before Next.js can complete its build process
     - Check the error logs for specific module resolution issues
     - Ensure all dependencies are properly installed
     - Try increasing Node.js memory limit with NODE_OPTIONS

3. **Vercel Environment**
   - Make sure Next.js is correctly installed and available
   - Set NODE_ENV=production in vercel.json
   - Enable legacy peer dependencies in .npmrc and vercel.json

## Backend (Render or other platforms)

### Package Hash Mismatch Issues

If you see package hash mismatch errors:
1. Use the requirements_no_hash.txt file for deployment
2. Run `pip install -r requirements_no_hash.txt` instead of the original requirements.txt
3. If hash verification is required, regenerate the requirements.txt with:
   ```
   pip install -r requirements_no_hash.txt
   pip freeze > requirements.txt
   ```

## Environment Variables

Ensure all necessary environment variables are set in both frontend and backend deployment environments.

## Deployment Steps

1. Commit and push all changes to your repository
2. Deploy the frontend to Vercel
3. Deploy the backend using requirements_no_hash.txt
4. Verify that all services are running correctly 