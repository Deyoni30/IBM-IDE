import os

from groq import Groq

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


def generer_explication(transaction, score, niveau):
    """
    Call the Groq chat completions API to produce a short French explanation
    (1–2 sentences) of why the transaction looks suspicious, aimed at a
    non-technical fraud analyst.

    Falls back to a safe string if the API key is absent or the call fails.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return f"Score {score}/4 - analyse automatique indisponible."

    prompt = (
        f"Tu es un expert en détection de fraude. Explique en 1 à 2 phrases courtes, "
        f"en français et de façon accessible à un analyste non-technique, pourquoi la "
        f"transaction suivante est suspecte.\n\n"
        f"Type : {transaction.type}\n"
        f"Montant : {transaction.amount}\n"
        f"Solde expéditeur avant : {transaction.sender_old_balance}, après : {transaction.sender_new_balance}\n"
        f"Solde destinataire avant : {transaction.receiver_old_balance}, après : {transaction.receiver_new_balance}\n"
        f"Score de risque : {score}/4\n"
        f"Niveau : {niveau}"
    )

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return f"Score {score}/4 - analyse automatique indisponible."
