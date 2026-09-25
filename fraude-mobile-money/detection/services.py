from .models import Transaction


def calculer_score(transaction):
    """
    Compute a fraud risk score (0–4) for a Transaction instance.

    Scoring rules are derived from statistical analysis of the PaySim synthetic
    mobile-money dataset, where fraudulent transactions are almost exclusively of
    type CASH_OUT or TRANSFER and exhibit characteristic balance anomalies:
    the sender drains their account, their resulting balance drops to zero, the
    receiver's starting balance is zero (mule account), and the bookkeeping
    difference between expected and actual new balance is negligible (≤ 1).
    """
    if transaction.type not in ('CASH_OUT', 'TRANSFER'):
        return 0

    score = 0

    # Sender empties (nearly) their full balance in one shot
    if transaction.sender_old_balance > 0 and transaction.amount >= transaction.sender_old_balance * 0.9:
        score += 1

    # Sender balance reaches exactly zero after the transaction
    if transaction.sender_new_balance == 0:
        score += 1

    # Receiver starts with an empty balance (mule / dormant account)
    if transaction.receiver_old_balance == 0:
        score += 1

    # Bookkeeping is consistent: expected new balance matches actual new balance
    if abs((transaction.sender_old_balance - transaction.amount) - transaction.sender_new_balance) <= 1:
        score += 1

    return score


def determiner_niveaux(score):
    """
    Map a fraud risk score returned by calculer_score() to a severity label.

    Returns:
        'CRITIQUE' for score 4 (highest risk),
        'ELEVE'    for score 3,
        'MOYEN'    for score 2,
        'FAIBLE'   for score 1,
        None       for score 0 (no risk detected).
    """
    levels = {
        4: 'CRITIQUE',
        3: 'ELEVE',
        2: 'MOYEN',
        1: 'FAIBLE',
        0: None,
    }
    return levels.get(score)
