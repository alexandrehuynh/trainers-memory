# API Key Schema and Authentication Fix Deployment Guide

This guide outlines the process for deploying fixes for API key schema issues and authentication problems.

## Overview

The primary issues we're addressing are:

1. Missing `user_id` column in the `api_keys` table
2. Improved API key validation with better error handling
3. Enhanced CORS configuration
4. More robust transaction management

## Pre-Deployment Tasks

Before applying these changes to production, follow these steps:

1. Back up your production database:

```bash
pg_dump -U your_db_user -h your_db_host -d your_db_name -f backup_before_fix.sql
```

2. Create a testing environment with a copy of the production database.

## Deployment Steps

### 1. Diagnostic Check

First, run the diagnostic script to check the state of the `api_keys` table:

```bash
cd backend
python check_api_keys_schema.py
```

This will show the current schema and any issues with the `api_keys` table.

### 2. Apply Database Migration

Run the Alembic migration to add the missing `user_id` column:

```bash
cd backend
alembic upgrade head
```

This will apply all pending migrations, including the `fix_api_keys_user_id` migration that adds the `user_id` column to the `api_keys` table.

### 3. Verify and Fix Data Issues

Run the verification script to identify and fix any issues with API keys:

```bash
cd backend
python scripts/verify_api_keys.py --fix
```

This will ensure all API keys have proper `user_id` associations.

### 4. Deploy Code Changes

Deploy the following updated files:

- `backend/app/auth_utils.py` - Improved API key validation
- `backend/app/db/repositories.py` - Enhanced API key repository
- `backend/app/main.py` - Updated CORS configuration

### 5. Post-Deployment Verification

After deploying the changes, run these tests to verify everything is working correctly:

1. Re-run the diagnostic script to confirm the schema is correct:

```bash
cd backend
python check_api_keys_schema.py
```

2. Test API key validation:

```bash
cd backend
python test_api_key.py
```

3. Check client creation through the frontend.

4. Verify workout fetching works properly.

## Rollback Plan

If issues arise during or after deployment, follow these steps to roll back:

1. Revert the code changes to the previous versions.

2. Restore the database from the backup:

```bash
psql -U your_db_user -h your_db_host -d your_db_name -f backup_before_fix.sql
```

## Monitoring

After deployment, monitor the application for:

1. 500 errors in the backend logs
2. CORS errors in the frontend console
3. Authentication failures
4. Transaction failures

## Future Improvements

To prevent similar issues in the future:

1. Implement a schema verification script that runs automatically as part of deployment.
2. Add more comprehensive tests for the authentication flow.
3. Create a database schema documentation that is kept up-to-date with migrations.
4. Consider implementing a more robust database schema versioning system.

## Contact

If you encounter any issues during deployment, contact [Your Name/Team]. 