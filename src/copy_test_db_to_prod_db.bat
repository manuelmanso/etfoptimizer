mongodump --host %MONGO_DB_HOST% --db test

mongo --host %MONGO_DB_HOST% prod --eval "db.dropDatabase()"

mongorestore --host %MONGO_DB_HOST% --db prod dump/test