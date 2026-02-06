FILE_NAME=$1
psql -h localhost -p 5432 -U postgres -d test -f ${FILE_NAME}
