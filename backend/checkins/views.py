from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.checkin_service import process_checkin
from .serializers import CheckInResponseSerializer


class CheckInView(APIView):
    """
    GET|POST /api/checkin/{token}/
    Validates token and checks guest in.
    Public endpoint for QR scans.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def _handle_checkin(self, request, token):
        result = process_checkin(
            token=str(token),
            user=request.user if getattr(request.user, "is_authenticated", False) else None,
        )

        if result["success"]:
            serializer = CheckInResponseSerializer(result["data"])
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response({"detail": result["error"]}, status=result["status_code"])

    def get(self, request, token):
        return self._handle_checkin(request, token)

    def post(self, request, token):
        return self._handle_checkin(request, token)
