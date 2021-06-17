mongodump --host %MONGO_DB_HOST%:%MONGO_DB_PORT% --db test

mongo --host %MONGO_DB_HOST%:%MONGO_DB_PORT% prod --eval "db.dropDatabase()"

mongorestore --host %MONGO_DB_HOST%:%MONGO_DB_PORT% --db prod dump/test