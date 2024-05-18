from typing import Optional, List, Dict
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
import json, os
import uvicorn

# bank_accounts dict to save the account details
# This dict will be dumped to the json file (which acts like a database)
bank_accounts = {}

class Payee(BaseModel):
    id: str
    name: str
    nickname: str
    account_id: str
    ifsc_code: str

class Account(BaseModel):
    id: str
    first_name: str
    last_name: str
    date_of_birth: str
    Address: str
    Nationality: str
    fathers_name: str
    mothers_name: str
    aadhar_id: str
    pan_id: str
    balance: float
    payee_list: Optional[Dict[str, Payee]] = {}

# FastAPI app instance
app = FastAPI()

def get_json_path():
    json_path = os.path.abspath(os.path.dirname(__file__))
    json_path = os.path.join(json_path, "bank_accounts.json")
    return json_path

def read_account_log():
    """
    To load the initial set of accounts from the json file (which acts as a database)
    """
    
    with open(get_json_path(), 'r') as account_log:
        global bank_accounts
        bank_accounts = json.load(account_log)

read_account_log()
def write_account_log():
    """
    To write the changes to the json file (database)
    """
    with open(get_json_path(), 'w') as account_log:
        global bank_accounts
        json.dump(bank_accounts, account_log, sort_keys=True, indent=4)

@app.post("/v1/account")
async def create_account(account: Account):
    if account.id in bank_accounts.keys():
        return {"message": "Account already exists"}
    bank_accounts[account.id] = account.dict()
    write_account_log()
    return account.dict()

@app.get("/v1/account/{account_id}")
async def read_account(account_id:str):
    if account_id not in bank_accounts.keys():
        return {"message": "Account does not exist"}
    return bank_accounts[account_id]

@app.put("/v1/account/{account_id}")
async def edit_account(account_id:str, account: Account):
    if account_id not in bank_accounts.keys():
        return {"message": "Account does not exist"}
    bank_accounts[account_id] = account.dict()
    write_account_log()
    return account.dict()

@app.delete("/v1/account/{account_id}")
async def create_account(account_id: str):
    del bank_accounts[account_id]
    write_account_log()
    return {'account_id': account_id,
            'message': "Account Deleted"}

@app.get("/v1/account/{account_id}/balance")
async def get_account_balance(account_id: str):
    return {'account_id': account_id, 'balance':bank_accounts[account_id]["balance"]}

@app.put("/v1/account/{account_id}/cash/deposit")
async def cash_deposit(account_id: str, amount: float = 0):
    bank_accounts[str(account_id)]["balance"] += amount
    write_account_log()
    return {'account_id': account_id, 'balance':bank_accounts[account_id]["balance"]}

@app.put("/v1/account/{account_id}/cash/withdraw")
async def cash_withdraw(account_id: str, amount: float = 0):
    bank_accounts[str(account_id)]["balance"] -= amount
    write_account_log()
    return {'account_id': account_id, 'balance':bank_accounts[account_id]["balance"]}

@app.post("/v1/account/{account_id}/payee")
async def add_payee(account_id: str, payee_details: Payee):
    selected_account = bank_accounts[account_id]
    if "payee_list" not in selected_account.keys():
        selected_account["payee_list"] = {}
    selected_account["payee_list"][payee_details.id] = payee_details.dict()
    write_account_log()
    return payee_details.dict()
 
@app.post("/v1/account/{account_id}/cash/transfer/{payee_id}")
async def cash_transfer(account_id: str, payee_id:str, amount: float = 0):
    selected_account = bank_accounts[account_id]
    selected_account["balance"] -= amount
    payee_account_id = str(selected_account["payee_list"][payee_id]["account_id"])
    bank_accounts[payee_account_id]["balance"] += amount
    write_account_log()
    return {'account_id': account_id, 'payee_account_id':payee_account_id,
            'current_balance':selected_account["balance"],
            'payee_balance': bank_accounts[payee_account_id]["balance"]}

@app.delete("/v1/account/{account_id}/payee/{payee_id}")
async def delete_payee(account_id: str, payee_id: str):
    selected_account = bank_accounts[account_id]
    selected_account["payee_list"].pop(payee_id, None)
    write_account_log()
    return {'account_id': account_id,
            'payee_id': payee_id}

def serve_bank_api():
    uvicorn.run(app, host='0.0.0.0', port=5000 )

if __name__ == "__main__":
    # Serve the app with uvicorn
    serve_bank_api()