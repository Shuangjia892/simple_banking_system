from banking_system import BankingSystem

def main():
    bank = BankingSystem()
    filepath = 'data.csv'
    bank.load_from_csv(filepath)

    try:
        bank.create_account("Alice", 1000)
        bank.create_account("Bob", 500)

        alice = bank.get_account("Alice")
        bob = bank.get_account("Bob")

        alice.deposit(200)
        alice.transfer_to(bob, 300)
        bob.withdraw(100)

        print(f"Alice's Balance: ${alice.balance}")
        print(f"Bob's Balance: ${bob.balance}")

        bank.save_to_csv(filepath)
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
