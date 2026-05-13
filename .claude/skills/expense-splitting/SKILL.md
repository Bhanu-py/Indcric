---
name: expense-splitting
description: Use when working on Splitwise-style group expense tracking in the IndCric app — beyond cricket session costs. Covers ExpenseGroup / Expense / ExpenseSplit models, equal vs custom splits, balance calculation (paid - owed), debt simplification, and wallet-based settlement (atomic credit + debit). Trigger when implementing /expenses/ URLs, expense entry forms, balance summary views, or any non-cricket group cost-sharing feature.
---

# Group Expense Splitting (Splitwise-style)

Use this skill when working on the group expense tracking and splitting features — beyond just cricket session costs.

## Feature Goal

Members should be able to:
1. Log an expense for any group event (dinner, travel, gear purchase, etc.)
2. Choose who participated and how to split (equal or custom amounts)
3. See a running balance: how much each person owes or is owed
4. Settle debts via wallet adjustments or mark as cash-settled

This mirrors Splitwise's core loop: log → split → settle.

## Proposed Data Model

```python
class ExpenseGroup(models.Model):
    """Optional: group expenses under a named event (e.g. 'Post-match dinner')"""
    name = models.CharField(max_length=255)
    date = models.DateField()
    session = models.ForeignKey('Session', null=True, blank=True, on_delete=models.SET_NULL)
    created_by = models.ForeignKey('User', on_delete=models.CASCADE)

class Expense(models.Model):
    group = models.ForeignKey(ExpenseGroup, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey('User', on_delete=models.CASCADE, related_name='expenses_paid')
    date = models.DateField(auto_now_add=True)

class ExpenseSplit(models.Model):
    """One row per (expense, participant) — how much each person owes"""
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='splits')
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    settled = models.BooleanField(default=False)
    settled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('expense', 'user')
```

## Balance Calculation

Net balance for a user = (sum of expenses they paid) - (sum of splits assigned to them).

```python
from django.db.models import Sum

def get_user_balance(user):
    paid = Expense.objects.filter(paid_by=user).aggregate(
        total=Sum('total_amount'))['total'] or 0
    owed = ExpenseSplit.objects.filter(user=user, settled=False).aggregate(
        total=Sum('amount'))['total'] or 0
    return paid - owed  # positive = others owe this user
```

To get simplified debts between pairs (who owes whom), use a debt simplification algorithm:
1. Compute net balance for each user
2. Users with negative balance owe money; positive balance are owed
3. Greedily match debtors to creditors

## Equal Split Helper

```python
def split_equally(expense, users):
    per_person = expense.total_amount / len(users)
    for user in users:
        ExpenseSplit.objects.create(
            expense=expense,
            user=user,
            amount=per_person
        )
```

## Settlement Flow

Option A — Wallet settlement:
```python
from django.db import transaction

@transaction.atomic
def settle_via_wallet(split):
    """Debtor's wallet is debited, creditor's wallet is credited."""
    Wallet.objects.create(user=split.user, amount=-split.amount, status='settled')
    Wallet.objects.create(user=split.expense.paid_by, amount=split.amount, status='settled')
    split.settled = True
    split.settled_at = timezone.now()
    split.save()
```

Option B — Cash settlement: just mark `split.settled = True`.

See the [payments-wallet](../payments-wallet/SKILL.md) skill for Wallet transaction conventions.

## URL Structure (suggested)

```
/expenses/                          # List all expense groups
/expenses/create/                   # Create new expense group
/expenses/<group_id>/               # Group detail: list expenses + balances
/expenses/<group_id>/add/           # Add expense to group
/expenses/<expense_id>/settle/      # Settle a split (HTMX POST)
/expenses/balances/                 # My overall balance summary
```

## Template Patterns

### Balance card
Show net balance prominently: green if positive (owed money), red if negative (owes money).

```html
{% if balance >= 0 %}
<span class="text-green-600">+{{ balance|floatformat:2 }}</span>
{% else %}
<span class="text-red-600">{{ balance|floatformat:2 }}</span>
{% endif %}
```

### Split entry (HTMX inline)
Use HTMX to dynamically add/remove split rows when creating an expense without full page reload.

## Integration with Session Payments

When `attendance_confirmed` for a session, optionally auto-create an `Expense` + `ExpenseSplit` records so the venue cost flows through the same expense ledger. This unifies session costs and ad-hoc expenses in one balance view.

## Testing Checklist
- [ ] Equal split divides correctly (handle odd cents via first-person adjustment)
- [ ] Custom splits must sum to total_amount (validate in form)
- [ ] Wallet settlement is atomic (both debit and credit succeed or neither does)
- [ ] Balance view aggregates all unsettled splits correctly
- [ ] Settled splits are excluded from outstanding balance
- [ ] User can only settle their own splits (not others')
