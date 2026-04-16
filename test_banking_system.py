import os
import tempfile
import unittest
from decimal import Decimal

from banking_system import (
    AccountNotFoundError,
    BankingSystem,
    DataFormatError,
    DuplicateAccountError,
    InsufficientFundsError,
    InvalidAmountError,
)

class TestBankingSystem(unittest.TestCase):
    def setUp(self):
        self.bank = BankingSystem()
        self.bank.create_account("Alice", 1000)
        self.bank.create_account("Bob", 500)

    def test_deposit(self):
        acc = self.bank.get_account("Alice")
        acc.deposit("200.10")
        self.assertEqual(acc.balance, Decimal("1200.10"))

    def test_withdraw(self):
        acc = self.bank.get_account("Bob")
        acc.withdraw("100.05")
        self.assertEqual(acc.balance, Decimal("399.95"))

    def test_overdraft(self):
        acc = self.bank.get_account("Bob")
        with self.assertRaises(InsufficientFundsError):
            acc.withdraw(600)

    def test_transfer(self):
        self.bank.transfer("Alice", "Bob", "300.25")
        alice = self.bank.get_account("Alice")
        bob = self.bank.get_account("Bob")
        self.assertEqual(alice.balance, Decimal("699.75"))
        self.assertEqual(bob.balance, Decimal("800.25"))

    def test_transaction_log_for_deposit_withdraw_transfer(self):
        self.bank.deposit("Alice", "20.00")
        self.bank.withdraw("Bob", "10.00")
        self.bank.transfer("Alice", "Bob", "5.00")

        txs = self.bank.get_transactions()
        tx_types = [tx["type"] for tx in txs]

        self.assertIn("DEPOSIT", tx_types)
        self.assertIn("WITHDRAW", tx_types)
        self.assertIn("TRANSFER", tx_types)

    def test_save_transactions_to_csv(self):
        self.bank.deposit("Alice", "50.00")

        with tempfile.TemporaryDirectory() as tmp_dir:
            filepath = os.path.join(tmp_dir, "transactions.csv")
            self.bank.save_transactions_to_csv(filepath)

            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()

            self.assertIn("timestamp,type,amount", content)
            self.assertIn("DEPOSIT", content)

    def test_decimal_precision(self):
        acc = self.bank.get_account("Alice")
        acc.deposit("0.10")
        acc.deposit("0.20")
        self.assertEqual(acc.balance, Decimal("1000.30"))

    def test_negative_starting_balance(self):
        with self.assertRaises(InvalidAmountError):
            self.bank.create_account("Eve", -1)

    def test_duplicate_account(self):
        with self.assertRaises(DuplicateAccountError):
            self.bank.create_account("Alice", 300)

    def test_nonexistent_account(self):
        with self.assertRaises(AccountNotFoundError):
            self.bank.get_account("Charlie")

    def test_csv_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            filepath = os.path.join(tmp_dir, "accounts.csv")
            self.bank.save_to_csv(filepath)

            loaded_bank = BankingSystem()
            loaded_bank.load_from_csv(filepath)

            self.assertEqual(loaded_bank.get_account("Alice").balance, Decimal("1000.00"))
            self.assertEqual(loaded_bank.get_account("Bob").balance, Decimal("500.00"))

    def test_csv_load_invalid_header(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            filepath = os.path.join(tmp_dir, "accounts.csv")
            with open(filepath, "w", encoding="utf-8") as file:
                file.write("username,amount\nAlice,100.00\n")

            with self.assertRaises(DataFormatError):
                self.bank.load_from_csv(filepath)

    def test_csv_load_duplicate_account(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            filepath = os.path.join(tmp_dir, "accounts.csv")
            with open(filepath, "w", encoding="utf-8") as file:
                file.write("name,balance\nAlice,100.00\nAlice,200.00\n")

            with self.assertRaises(DuplicateAccountError):
                self.bank.load_from_csv(filepath)

    def test_load_failure_is_transactional(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            filepath = os.path.join(tmp_dir, "accounts.csv")
            with open(filepath, "w", encoding="utf-8") as file:
                file.write("name,balance\nAlice,100.00\nBob,INVALID\n")

            with self.assertRaises(InvalidAmountError):
                self.bank.load_from_csv(filepath)

            # existing state is unchanged when loading fails
            self.assertEqual(self.bank.get_account("Alice").balance, Decimal("1000.00"))
            self.assertEqual(self.bank.get_account("Bob").balance, Decimal("500.00"))

if __name__ == '__main__':
    unittest.main()
