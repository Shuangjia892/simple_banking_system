from banking_system import BankingError, BankingSystem


def _print_menu():
    print("\n=== Simple Banking System ===")
    print("1. Create account")
    print("2. Deposit")
    print("3. Withdraw")
    print("4. Transfer")
    print("5. Show balances")
    print("6. Show recent transactions")
    print("7. Save and exit")


def _show_balances(bank):
    if not bank.accounts:
        print("No accounts yet.")
        return
    print("\nCurrent balances:")
    for name, account in sorted(bank.accounts.items()):
        print(f"- {name}: ${account.balance}")


def _show_transactions(bank, limit=10):
    transactions = bank.get_transactions(limit=limit)
    if not transactions:
        print("No transactions yet.")
        return
    print(f"\nRecent {len(transactions)} transaction(s):")
    for tx in transactions:
        print(
            f"[{tx['timestamp']}] {tx['type']} amount=${tx['amount']} "
            f"from={tx['source_account'] or '-'} to={tx['target_account'] or '-'} status={tx['status']}"
        )


def main():
    bank = BankingSystem()
    accounts_file = "data.csv"
    transactions_file = "transactions.csv"
    bank.load_from_csv(accounts_file)

    while True:
        _print_menu()
        choice = input("Choose an option (1-7): ").strip()

        try:
            if choice == "1":
                name = input("Account name: ").strip()
                balance = input("Starting balance: ").strip()
                bank.create_account(name, balance)
                print("Account created.")
            elif choice == "2":
                name = input("Account name: ").strip()
                amount = input("Deposit amount: ").strip()
                bank.deposit(name, amount)
                print("Deposit successful.")
            elif choice == "3":
                name = input("Account name: ").strip()
                amount = input("Withdraw amount: ").strip()
                bank.withdraw(name, amount)
                print("Withdraw successful.")
            elif choice == "4":
                from_name = input("From account: ").strip()
                to_name = input("To account: ").strip()
                amount = input("Transfer amount: ").strip()
                bank.transfer(from_name, to_name, amount)
                print("Transfer successful.")
            elif choice == "5":
                _show_balances(bank)
            elif choice == "6":
                _show_transactions(bank)
            elif choice == "7":
                bank.save_to_csv(accounts_file)
                bank.save_transactions_to_csv(transactions_file)
                print("Data saved. Bye!")
                break
            else:
                print("Invalid option, please choose 1-7.")
        except BankingError as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()
