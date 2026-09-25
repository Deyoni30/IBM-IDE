import io
from collections import Counter

import pandas as pd
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Alerte, Transaction
from .services import calculer_score, determiner_niveaux


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

class AlerteSerializer(serializers.ModelSerializer):
    transaction_type = serializers.CharField(source="transaction.type", read_only=True)
    transaction_amount = serializers.DecimalField(
        source="transaction.amount", max_digits=15, decimal_places=2, read_only=True
    )
    transaction_sender_id = serializers.CharField(source="transaction.sender_id", read_only=True)
    transaction_receiver_id = serializers.CharField(source="transaction.receiver_id", read_only=True)

    class Meta:
        model = Alerte
        fields = [
            "id",
            "score",
            "niveau",
            "explication",
            "created_at",
            "transaction_type",
            "transaction_amount",
            "transaction_sender_id",
            "transaction_receiver_id",
        ]


# ---------------------------------------------------------------------------
# Alerte list view
# ---------------------------------------------------------------------------

NIVEAU_VALUES = {"FAIBLE", "MOYEN", "ELEVE", "CRITIQUE"}


class AlerteListView(ListAPIView):
    """
    GET /api/alertes/

    Returns all Alerte objects ordered by created_at descending.
    Optional query parameter:
        niveau=FAIBLE|MOYEN|ELEVE|CRITIQUE  — filters to that level only.
    Pagination: 20 items per page (DRF PageNumberPagination).
    """

    serializer_class = AlerteSerializer

    def get_queryset(self):
        qs = Alerte.objects.select_related("transaction").order_by("-created_at")
        niveau = self.request.query_params.get("niveau")
        if niveau is not None:
            if niveau not in NIVEAU_VALUES:
                return Alerte.objects.none()
            qs = qs.filter(niveau=niveau)
        return qs

MAX_ROWS = 1000

# Mapping from CSV column names to Transaction field names
CSV_COLUMNS = {
    "type":           "type",
    "amount":         "amount",
    "nameOrig":       "sender_id",
    "oldbalanceOrg":  "sender_old_balance",
    "newbalanceOrig": "sender_new_balance",
    "nameDest":       "receiver_id",
    "oldbalanceDest": "receiver_old_balance",
    "newbalanceDest": "receiver_new_balance",
}


class UploadCSVView(APIView):
    """
    POST /api/upload/

    Accept a multipart/form-data request with a single field named ``file``
    containing a PaySim-formatted CSV.  Only the first 1 000 rows are
    processed.  For every row a Transaction is created, scored with
    calculer_score(), and — when the score is ≥ 1 — an Alerte is created.

    Response (JSON):
        {
            "total":   <int>,          # rows processed
            "alertes": <int>,          # Alerte objects created
            "breakdown": {
                "FAIBLE":    <int>,
                "MOYEN":     <int>,
                "ELEVE":     <int>,
                "CRITIQUE":  <int>
            }
        }
    """

    parser_classes = [MultiPartParser]

    def post(self, request):
        csv_file = request.FILES.get("file")
        if csv_file is None:
            return Response({"error": "No file uploaded. Use field name 'file'."}, status=400)

        # Read into memory so pandas never touches the file system
        try:
            df = pd.read_csv(io.BytesIO(csv_file.read()), nrows=MAX_ROWS)
        except Exception as exc:
            return Response({"error": f"Could not parse CSV: {exc}"}, status=400)

        missing = [col for col in CSV_COLUMNS if col not in df.columns]
        if missing:
            return Response(
                {"error": f"Missing required column(s): {', '.join(missing)}"},
                status=400,
            )

        niveau_counts: Counter = Counter()
        alerte_count = 0

        for _, row in df.iterrows():
            transaction = Transaction(
                type=row["type"],
                amount=row["amount"],
                sender_id=row["nameOrig"],
                sender_old_balance=row["oldbalanceOrg"],
                sender_new_balance=row["newbalanceOrig"],
                receiver_id=row["nameDest"],
                receiver_old_balance=row["oldbalanceDest"],
                receiver_new_balance=row["newbalanceDest"],
            )
            transaction.save()

            score = calculer_score(transaction)
            transaction.score = score
            transaction.save(update_fields=["score"])

            if score >= 1:
                niveau = determiner_niveaux(score)
                Alerte.objects.create(
                    transaction=transaction,
                    score=score,
                    niveau=niveau,
                )
                niveau_counts[niveau] += 1
                alerte_count += 1

        return Response(
            {
                "total": len(df),
                "alertes": alerte_count,
                "breakdown": {
                    "FAIBLE":   niveau_counts.get("FAIBLE", 0),
                    "MOYEN":    niveau_counts.get("MOYEN", 0),
                    "ELEVE":    niveau_counts.get("ELEVE", 0),
                    "CRITIQUE": niveau_counts.get("CRITIQUE", 0),
                },
            },
            status=201,
        )
