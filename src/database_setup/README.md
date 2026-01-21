    If already in azure-project2 then run these to create tables in db.
psql -U postgres -d postgres -c "CREATE DATABASE project_db;"
psql -U postgres -d project_db -f sql/database.sql
    it should create three tables after having created the database
    now run populate.py and it will fill the database with fake data
--------------------------------------------------------------------------
    ****obs: need to create database.ini file following:****
    [postgresql]
    host=localhost
    database=project_db
    port=5432
    user=postgres
    password=Penguinz3
python sql/populate.py
a