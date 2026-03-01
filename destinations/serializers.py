from rest_framework import serializers
from .models import Destination


class DestinationSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = ["id", "city", "country", "label"]

    def get_label(self, obj):
        return f"{obj.city}, {obj.country}"