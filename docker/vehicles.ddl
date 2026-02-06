-- public.vehicles definition

-- Drop table

-- DROP TABLE public.vehicles;

CREATE TABLE public.vehicles (
	id UUID NOT NULL,
	city VARCHAR NOT NULL,
	type VARCHAR NULL,
	owner_id UUID NULL,
	creation_time TIMESTAMP NULL,
	status VARCHAR NULL,
	current_location VARCHAR NULL,
	ext JSONB NULL,
	CONSTRAINT vehicles_pkey PRIMARY KEY (city ASC, id ASC),
	CONSTRAINT vehicles_city_owner_id_fkey FOREIGN KEY (city, owner_id) REFERENCES public.users(city, id),
	CONSTRAINT fk_owner_ref_users FOREIGN KEY (city, owner_id) REFERENCES public.users(city, id),
	INDEX vehicles_auto_index_fk_city_ref_users (city ASC, owner_id ASC)
);


-- public.vehicles foreign keys

ALTER TABLE public.vehicles ADD CONSTRAINT fk_owner_ref_users FOREIGN KEY (city,owner_id) REFERENCES public."users"(city,id);
ALTER TABLE public.vehicles ADD CONSTRAINT vehicles_city_owner_id_fkey FOREIGN KEY (city,owner_id) REFERENCES public."users"(city,id);
