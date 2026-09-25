import pandas as pd 
df = pd.read_csv('data/paysim.csv')
print(f"Total transactions : {len(df)}")

def score_suspiction(row):
    score = 0

    # Filtre obligatoire : seul ces filtre on montrer de la fraude
    if row['type'] not in ['CASH_OUT', 'TRANSFER']:
        return 0

    # Signale 1: montant eleve (seuil  = 3x la moyenne normale)  
    if row['oldbalanceOrg'] > 0 and row['amount'] >= row['oldbalanceOrg'] * 0.9:
        score += 1

    # Signale 2: solde emetteur vide a 0 apres la transactions
    if row['newbalanceOrig'] == 0:
        score += 1

    # Signale 3: solde destinataire a 0 avant reception
    if  row['oldbalanceDest'] == 0:    
        score += 1

    # Signal 4: coherence comptable parfaite   
    ecart = abs((row['oldbalanceOrg'] - row['amount']) - row['newbalanceOrig'])
    if ecart <= 1:
        score += 1 
    return score   

print("Calcul des scores en cours...")
df['score'] = df.apply(score_suspiction, axis = 1) 
print("Termine.")
print(df['score'].value_counts())   
print("\n--- Croisement score vs isFraud reel ---")
print(df.groupby(['score', 'isFraud']).size())
# print("\n--- Test incoherence comptable emetteur ---")
# df['ecart_orig'] = abs((df['oldbalanceOrg'] - df['amount']) - df['newbalanceOrig'])
# fraud = df[df['isFraud'] == 1]
# normal = df[df['isFraud'] == 0]
# print("Fraude - % avec ecart > 1 :", (fraud['ecart_orig'] > 1).mean())
# print("Normal - % avec ecart > 1 :", (normal['ecart_orig'] > 1).mean())
