---
name: payments-wallet
description: Use when working on Payment, Wallet, or session cost-splitting features in the IndCric Django app. Covers per-session Payment records (status, method), Wallet transaction log (running balance from summed rows), Decimal handling for money, and atomic wallet+payment transactions. Trigger on edits to Payment/Wallet models, payment views, wallet top-up flows, or any code touching `session.cost_per_person`, `Payment.status`, or `Wallet.amount`.
---

# Payments & Wallet

Use this skill when working on payment tracking, wallet balances, session cost splitting, or any money-related feature.

## Context

The app tracks two payment flows:

**1. Session payments** — After a session is confirmed, the per-person cost is split across attendees. Each attendee gets a `Payment` record (unique per user+session). Method is `cash` or `wallet`.

**2. Wallet** — A running balance per user. Transactions are stored as `Wallet` rows (positive = top-up, negative = deduction). The current balance is the sum of all rows for that user.

## Key Models

```python
# Payment: one record per (user, session)
Payment.status   = 'pending' | 'paid'
Payment.method   = 'wallet' | 'cash'

# Wallet: transaction log (sum = current balance)
Wallet.amount    = Decimal  # positive = credit, negative = debit
Wallet.status    = 'pending' | ...
```

## Common Patterns

### Calculate wallet balance
```python
from django.db.models import Sum
balance = Wallet.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or 0
```

### Deduct session cost from wallet
```python
from decimal import Decimal
Wallet.objects.create(user=user, amount=-session.cost_per_person, status='paid')
payment.method = 'wallet'
payment.status = 'paid'
payment.save()
```

### Auto-create payments when attendance confirmed
When `session.attendance_confirmed` flips to True:
1. Recalculate `session.cost_per_person = session.cost / attendee_count`
2. For each SessionPlayer with `attended=True`: create or update their Payment

### HTMX payment toggle
Views that toggle payment status should return a partial re-rendering the payment row, not a full redirect. Check `request.htmx` and return the partial if true.

## Wallet Top-Up Flow (to implement)
1. Staff creates a `Wallet` credit transaction for user
2. User sees updated balance in profile
3. Balance is deducted automatically when session cost is charged

## Group Expense Splitting (Splitwise-style — to implement)
Beyond cricket sessions, players should be able to:
- Create an `Expense` with description, total amount, payer (user), and date
- Assign splits to each participant (equal or custom amounts)
- Settle via wallet balance adjustments
- View net balances: who owes whom

Suggested new models:
```python
class Expense(models.Model):
    description = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    session = models.ForeignKey(Session, null=True, blank=True, on_delete=models.SET_NULL)

class ExpenseSplit(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='splits')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    settled = models.BooleanField(default=False)
```

See the [expense-splitting](../expense-splitting/SKILL.md) skill for the full Splitwise-style design.

## Non-negotiables

- **Always use `Decimal`** for money — never `float`. Import `from decimal import Decimal`.
- **Wallet deduction + Payment status update must be atomic.** Wrap in `transaction.atomic()` so a half-write can't leave the user paid without a wallet deduction (or vice versa).
- **Staff-only mutations.** Any view that changes a Payment or creates a Wallet row should be `@staff_member_required` unless it's the user's own self-service action.

## Testing Checklist
- [ ] Payment created for every attending player when attendance confirmed
- [ ] Wallet balance never goes negative without warning
- [ ] Wallet deduction + payment status update are in a single `transaction.atomic()` block
- [ ] Staff can manually override payment status
- [ ] Payment method shown correctly in session detail view
