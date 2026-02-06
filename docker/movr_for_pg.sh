#!/bin/bash

# Configuration - update these if needed
DB_NAME="movr"
PG_USER="postgres" # Change to your postgres username

echo "🐘 Starting PostgreSQL setup for $DB_NAME..."

# 1. Create the database if it doesn't exist
# We connect to the default 'postgres' database to perform this check
DB_EXISTS=$(psql -U $PG_USER  -h localhost -p 5432 -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; echo $?)

if [ $DB_EXISTS -ne 0 ]; then
    echo "🛠️ Creating database: $DB_NAME..."
    psql -U $PG_USER -h localhost -p 5432 -c "CREATE DATABASE $DB_NAME;"
else
    echo "✅ Database $DB_NAME already exists."
fi

# 2. Run the DDL script
echo "📝 Creating tables in $DB_NAME..."

psql -U $PG_USER -h localhost -p 5432 -d $DB_NAME << 'EOF'

-- DROP existing tables to ensure a clean run
DROP TABLE IF EXISTS public.rides;
DROP TABLE IF EXISTS public.users;
DROP TABLE IF EXISTS public.vehicles;

-- Define public.users
CREATE TABLE public.users (
    id UUID NOT NULL,
    city VARCHAR NOT NULL,
    name VARCHAR NULL,
    address VARCHAR NULL,
    credit_card VARCHAR NULL,
    CONSTRAINT users_pkey PRIMARY KEY (city, id)
);

-- Define public.vehicles
CREATE TABLE public.vehicles (
    id UUID NOT NULL,
    city VARCHAR NOT NULL,
    type VARCHAR NULL,
    owner_id UUID NULL,
    creation_time TIMESTAMP NULL,
    status VARCHAR NULL,
    current_location VARCHAR NULL,
    ext JSONB NULL,
    CONSTRAINT vehicles_pkey PRIMARY KEY (city, id)
);

-- Create index for vehicles (fixed from inline Cockroach syntax)
CREATE INDEX vehicles_auto_index_fk_city_ref_users ON public.vehicles (city, owner_id);

-- Define public.rides
CREATE TABLE public.rides (
    id UUID NOT NULL,
    city VARCHAR NOT NULL,
    vehicle_city VARCHAR NULL,
    rider_id UUID NULL,
    vehicle_id UUID NULL,
    start_address VARCHAR NULL,
    end_address VARCHAR NULL,
    start_time TIMESTAMP NULL,
    end_time TIMESTAMP NULL,
    revenue DECIMAL(10,2) NULL,
    CONSTRAINT rides_pkey PRIMARY KEY (city, id),
    CONSTRAINT check_vehicle_city_city CHECK (vehicle_city = city)
);

-- Create indexes for rides (fixed from inline Cockroach syntax)
CREATE INDEX rides_auto_index_fk_city_ref_users ON public.rides (city, rider_id);
CREATE INDEX rides_auto_index_fk_vehicle_city_ref_vehicles ON public.rides (vehicle_city, vehicle_id);
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

EOF

echo "🚀 Setup complete. Tables created in $DB_NAME without Foreign Keys."
