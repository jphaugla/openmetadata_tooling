# getComposeFiles.sh
export VERSION=1.11.4
curl -sL -o docker-compose.yml "https://github.com/open-metadata/OpenMetadata/releases/download/${VERSION}-release/docker-compose.yml"
curl -sL -o docker-compose-postgres.yml https://github.com/open-metadata/OpenMetadata/releases/download/${VERSION}-release/docker-compose-postgres.yml
