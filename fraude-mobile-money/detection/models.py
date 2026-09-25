from django.db import models
class Transaction(models.Model):
    TYPE_CHOICE =[
        ('CASH_OUT', 'Cash Out'),
        ('TRANSFER', 'Transfer'),
        ('PAYMENT', 'Payment'),
        ('DEBIT', 'Debit'),
        ('CASH_IN', 'Cash In'),
    ]
    type =  models.CharField(max_length=20, choices=TYPE_CHOICE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    sender_id =  models.CharField(max_length=50)
    sender_old_balance = models.DecimalField(max_digits=15, decimal_places=2)
    sender_new_balance = models.DecimalField(max_digits=15, decimal_places=2)

    receiver_id =  models.CharField(max_length=50)
    receiver_old_balance = models.DecimalField(max_digits=15, decimal_places=2)
    receiver_new_balance = models.DecimalField(max_digits=15, decimal_places=2)
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.amount} - ({self.sender_id} - {self.receiver_id})"


class Alerte(models.Model):      
    NIVEAU_CHOICES = [
        ('Faible', 'Faible'),
        ('MOYEN', 'Moyen'),
        ('ELEVE', 'Eleve'),
        ('CRITIQUE', 'Critique'),
    ]  
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name = 'alertes')
    score = models.IntegerField()
    niveau = models.CharField(max_length=10, choices=NIVEAU_CHOICES)
    explication = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Alerte {self.niveau} - Transaction #{self.transaction.id}"
# Create your models here.

