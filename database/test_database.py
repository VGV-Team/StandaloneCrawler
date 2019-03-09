from database_interface import DatabaseInterface

DB = DatabaseInterface(config_path='database.ini')
row_id = DB.add_domain("test domain", "robotz", "sajtmep")
if row_id is not None:
    print("TEST: Inserted test row with id", row_id)
else:
    print("INSERT failed")
