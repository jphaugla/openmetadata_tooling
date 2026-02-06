USE movr;

-- 1. Vehicles to Users (Reference city + id)
ALTER TABLE vehicles 
DROP CONSTRAINT fk_owner_ref_users ;

-- 2. Rides to Vehicles (Reference city + id)
ALTER TABLE rides 
DROP CONSTRAINT fk_city_vehicle_ref_vehicles ;

-- 3. Rides to Users (Reference city + id)
ALTER TABLE rides 
DROP CONSTRAINT fk_rider_ref_users ;

-- 4. Vehicle Location Histories to Rides
ALTER TABLE vehicle_location_histories 
DROP CONSTRAINT fk_city_ride_ref_rides ;
