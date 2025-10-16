-- Initialize PostgreSQL database for MATLAB Automation Platform

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- Create database if not exists (this will be handled by docker-compose)
-- CREATE DATABASE matlab_automation;

-- Set timezone
SET timezone = 'UTC';

-- Create initial admin user (will be created by application)
-- This is just a placeholder for any initial setup
