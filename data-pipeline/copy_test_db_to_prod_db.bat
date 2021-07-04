mongodump --host %MONGO_DB_HOST%:2717 --db test

mongo --host %MONGO_DB_HOST%:2717 prod --eval "db.dropDatabase()"

mongorestore --host %MONGO_DB_HOST%:2717 --db prod dump/test