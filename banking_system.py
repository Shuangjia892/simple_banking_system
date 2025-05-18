import csv
import os

class Account:
    def __init__(self, name, balance=0.0):
        self.name = name
        self.balance = float(balance)

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Withdraw amount must be positive")
        if self.balance < amount:
            raise ValueError("Insufficient funds")
        self.balance -= amount

    def transfer_to(self, target_account, amount):
        self.withdraw(amount)
        target_account.deposit(amount)


class BankingSystem:
    def __init__(self):
        self.accounts = {}

    def create_account(self, name, starting_balance=0.0):
        if name in self.accounts:
            raise ValueError("Account already exists")
        self.accounts[name] = Account(name, starting_balance)

    def get_account(self, name):
        if name not in self.accounts:
            raise ValueError("Account not found")
        return self.accounts[name]

    def save_to_csv(self, filepath):
        with open(filepath, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['name', 'balance'])
            for account in self.accounts.values():
                writer.writerow([account.name, account.balance])

    def load_from_csv(self, filepath):
        if not os.path.exists(filepath):
            return
        with open(filepath, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                self.create_account(row['name'], float(row['balance']))
