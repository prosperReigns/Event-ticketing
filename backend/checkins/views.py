from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from core.services.checkin_service import process_checkin
from .serializers import CheckInResponseSerializer


class CheckInView(APIView):
    """
    GET /api/checkin/{token}/
    Validates token and checks guest in.
    Public endpoint – staff scan QR codes without authentication.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        result = process_checkin(token=str(token), user=request.user if request.user.is_authenticated else None)

        if result["success"]:
            serializer = CheckInResponseSerializer(result["data"])
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response({"detail": result["error"]}, status=result["status_code"])
