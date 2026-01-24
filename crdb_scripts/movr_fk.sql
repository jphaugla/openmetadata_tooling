USE movr;

-- 1. Vehicles to Users (Reference city + id)
ALTER TABLE vehicles 
ADD CONSTRAINT fk_owner_ref_users 
FOREIGN KEY (city, owner_id) REFERENCES users (city, id);

-- 2. Rides to Vehicles (Reference city + id)
ALTER TABLE rides 
ADD CONSTRAINT fk_city_vehicle_ref_vehicles 
FOREIGN KEY (city, vehicle_id) REFERENCES vehicles (city, id);

-- 3. Rides to Users (Reference city + id)
ALTER TABLE rides 
ADD CONSTRAINT fk_rider_ref_users 
FOREIGN KEY (city, rider_id) REFERENCES users (city, id);
