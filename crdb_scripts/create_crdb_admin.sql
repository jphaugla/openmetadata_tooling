create user if not exists jhaugland with login password 'jasonrocks';
grant all on database defaultdb to jhaugland;
grant admin to jhaugland;
ALTER ROLE jhaugland SET allow_unsafe_internals = true;
