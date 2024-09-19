from django.db import models
import uuid

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    # job = models.OneToOneField('jobs.JobPost', on_delete=models.CASCADE)
    job = models.OneToOneField('jobs.JobPost', on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    card_mask = models.CharField(max_length=20, null=True, blank=True)
    card_name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.status}"

    class Meta:
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['status']),
        ]
