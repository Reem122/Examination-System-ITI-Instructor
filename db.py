import pyodbc

def create_connection(driver="ODBC Driver 17 for SQL Server", server=".", db="ITI_GP", uid="rere", pwd="rere"):
    conn = pyodbc.connect(f"DRIVER={{{driver}}};SERVER={server};DATABASE={db};TRUST_CONNECTION=yes;ENCRYPT=NO;UID={uid};PWD={pwd}")
    return conn

def login(conn, email, password):
    result = conn.execute(f"EXEC dbo.LoginIN @Email='{email}', @Password='{password}'").fetchall()[0][0]
    return result
