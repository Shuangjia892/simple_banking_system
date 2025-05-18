import unittest
from banking_system import BankingSystem

class TestBankingSystem(unittest.TestCase):
    def setUp(self):
        self.bank = BankingSystem()
        self.bank.create_account("Alice", 1000)
        self.bank.create_account("Bob", 500)

    def test_deposit(self):
        acc = self.bank.get_account("Alice")
        acc.deposit(200)
        self.assertEqual(acc.balance, 1200)

    def test_withdraw(self):
        acc = self.bank.get_account("Bob")
        acc.withdraw(100)
        self.assertEqual(acc.balance, 400)

    def test_overdraft(self):
        acc = self.bank.get_account("Bob")
        with self.assertRaises(ValueError):
            acc.withdraw(600)

    def test_transfer(self):
        alice = self.bank.get_account("Alice")
        bob = self.bank.get_account("Bob")
        alice.transfer_to(bob, 300)
        self.assertEqual(alice.balance, 700)
        self.assertEqual(bob.balance, 800)

    def test_duplicate_account(self):
        with self.assertRaises(ValueError):
            self.bank.create_account("Alice", 300)

    def test_nonexistent_account(self):
        with self.assertRaises(ValueError):
            self.bank.get_account("Charlie")

if __name__ == '__main__':
    unittest.main()
