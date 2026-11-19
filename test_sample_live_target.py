def retrieve_user_account(account_id: str):
    # Live PR test comment target
    query = f"SELECT * FROM accounts WHERE id = '{account_id}'"
    return db.execute(query)
