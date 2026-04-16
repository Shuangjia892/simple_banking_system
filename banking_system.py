import csv
import os
import tempfile
import threading
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


TWOPLACES = Decimal("0.01")


class BankingError(Exception):
    """Base class for banking domain errors."""


class AccountNotFoundError(BankingError):
    pass


class DuplicateAccountError(BankingError):
    pass


class InvalidAmountError(BankingError):
    pass


class InvalidAccountNameError(BankingError):
    pass


class InsufficientFundsError(BankingError):
    pass


class DataFormatError(BankingError):
    pass


def _to_amount(value):
    try:
        amount = Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise InvalidAmountError("Amount must be a valid number") from exc
    return amount


def _normalize_name(name):
    if not isinstance(name, str) or not name.strip():
        raise InvalidAccountNameError("Account name must be a non-empty string")
    return name.strip()


class Account:
    def __init__(self, name, balance=Decimal("0.00")):
        self.name = _normalize_name(name)
        self.balance = _to_amount(balance)
        self._lock = threading.RLock()

    def deposit(self, amount):
        amount = _to_amount(amount)
        if amount <= Decimal("0.00"):
            raise InvalidAmountError("Deposit amount must be positive")
        with self._lock:
            self.balance += amount
            self.balance = self.balance.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    def withdraw(self, amount):
        amount = _to_amount(amount)
        if amount <= Decimal("0.00"):
            raise InvalidAmountError("Withdraw amount must be positive")
        with self._lock:
            if self.balance < amount:
                raise InsufficientFundsError("Insufficient funds")
            self.balance -= amount
            self.balance = self.balance.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    def transfer_to(self, target_account, amount):
        if not isinstance(target_account, Account):
            raise BankingError("Target account must be an Account instance")
        amount = _to_amount(amount)
        if amount <= Decimal("0.00"):
            raise InvalidAmountError("Transfer amount must be positive")

        first, second = sorted([self, target_account], key=lambda acc: acc.name)
        with first._lock:
            with second._lock:
                if self.balance < amount:
                    raise InsufficientFundsError("Insufficient funds")
                self.balance -= amount
                target_account.balance += amount
                self.balance = self.balance.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
                target_account.balance = target_account.balance.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


class BankingSystem:
    def __init__(self):
        self.accounts = {}
        self.transactions = []
        self._lock = threading.RLock()

    def _record_transaction(
        self,
        tx_type,
        amount=Decimal("0.00"),
        source_account="",
        target_account="",
        before_balance_source="",
        after_balance_source="",
        before_balance_target="",
        after_balance_target="",
        status="SUCCESS",
        message="",
    ):
        self.transactions.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": tx_type,
                "amount": f"{_to_amount(amount):.2f}",
                "source_account": source_account,
                "target_account": target_account,
                "before_balance_source": before_balance_source,
                "after_balance_source": after_balance_source,
                "before_balance_target": before_balance_target,
                "after_balance_target": after_balance_target,
                "status": status,
                "message": message,
            }
        )

    def create_account(self, name, starting_balance=Decimal("0.00")):
        normalized_name = _normalize_name(name)
        starting_balance = _to_amount(starting_balance)
        if starting_balance < Decimal("0.00"):
            raise InvalidAmountError("Starting balance cannot be negative")

        with self._lock:
            if normalized_name in self.accounts:
                raise DuplicateAccountError("Account already exists")
            self.accounts[normalized_name] = Account(normalized_name, starting_balance)
            self._record_transaction(
                tx_type="CREATE_ACCOUNT",
                amount=starting_balance,
                target_account=normalized_name,
                after_balance_target=f"{starting_balance:.2f}",
            )

    def get_account(self, name):
        normalized_name = _normalize_name(name)
        with self._lock:
            if normalized_name not in self.accounts:
                raise AccountNotFoundError("Account not found")
            return self.accounts[normalized_name]

    def transfer(self, from_name, to_name, amount):
        source = self.get_account(from_name)
        target = self.get_account(to_name)
        amount = _to_amount(amount)
        source_before = source.balance
        target_before = target.balance
        source.transfer_to(target, amount)
        self._record_transaction(
            tx_type="TRANSFER",
            amount=amount,
            source_account=source.name,
            target_account=target.name,
            before_balance_source=f"{source_before:.2f}",
            after_balance_source=f"{source.balance:.2f}",
            before_balance_target=f"{target_before:.2f}",
            after_balance_target=f"{target.balance:.2f}",
        )

    def deposit(self, name, amount):
        account = self.get_account(name)
        amount = _to_amount(amount)
        before = account.balance
        account.deposit(amount)
        self._record_transaction(
            tx_type="DEPOSIT",
            amount=amount,
            target_account=account.name,
            before_balance_target=f"{before:.2f}",
            after_balance_target=f"{account.balance:.2f}",
        )

    def withdraw(self, name, amount):
        account = self.get_account(name)
        amount = _to_amount(amount)
        before = account.balance
        account.withdraw(amount)
        self._record_transaction(
            tx_type="WITHDRAW",
            amount=amount,
            source_account=account.name,
            before_balance_source=f"{before:.2f}",
            after_balance_source=f"{account.balance:.2f}",
        )

    def get_transactions(self, limit=None):
        if limit is None:
            return list(self.transactions)
        return list(self.transactions[-limit:])

    def save_to_csv(self, filepath):
        directory = os.path.dirname(os.path.abspath(filepath)) or "."
        os.makedirs(directory, exist_ok=True)

        with self._lock:
            with tempfile.NamedTemporaryFile(mode="w", newline="", delete=False, dir=directory) as tmp_file:
                writer = csv.writer(tmp_file)
                writer.writerow(["name", "balance"])
                for account in self.accounts.values():
                    writer.writerow([account.name, f"{account.balance:.2f}"])
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                temp_path = tmp_file.name
            os.replace(temp_path, filepath)

    def load_from_csv(self, filepath):
        if not os.path.exists(filepath):
            return

        loaded_accounts = {}
        try:
            with open(filepath, mode="r", newline="") as file:
                reader = csv.DictReader(file)
                if "name" not in reader.fieldnames or "balance" not in reader.fieldnames:
                    raise DataFormatError("CSV must contain 'name' and 'balance' columns")

                for row in reader:
                    name = _normalize_name(row.get("name"))
                    balance = _to_amount(row.get("balance"))
                    if balance < Decimal("0.00"):
                        raise InvalidAmountError("Loaded balance cannot be negative")
                    if name in loaded_accounts:
                        raise DuplicateAccountError(f"Duplicate account in file: {name}")
                    loaded_accounts[name] = Account(name, balance)
        except OSError as exc:
            raise DataFormatError("Failed to read account data file") from exc

        with self._lock:
            self.accounts = loaded_accounts

    def save_transactions_to_csv(self, filepath):
        directory = os.path.dirname(os.path.abspath(filepath)) or "."
        os.makedirs(directory, exist_ok=True)
        fieldnames = [
            "timestamp",
            "type",
            "amount",
            "source_account",
            "target_account",
            "before_balance_source",
            "after_balance_source",
            "before_balance_target",
            "after_balance_target",
            "status",
            "message",
        ]

        with self._lock:
            with tempfile.NamedTemporaryFile(mode="w", newline="", delete=False, dir=directory) as tmp_file:
                writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.transactions)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                temp_path = tmp_file.name
            os.replace(temp_path, filepath)
