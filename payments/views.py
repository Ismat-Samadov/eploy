# payments/views.py
import os
import json
import base64
import hashlib
from uuid import uuid4
from django.shortcuts import redirect, render
from django.http import JsonResponse
import requests
from dotenv import load_dotenv
from .models import Order

# Load .env file to access sensitive data
load_dotenv()

# Retrieve sensitive data from .env file
PUBLIC_KEY = os.getenv('PUBLIC_KEY')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
EPOINT_API_URL = 'https://epoint.az/api/1/request'

def create_payment(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')

        # Generate unique order_id
        order_id = str(uuid4())

        # Save the order to the database
        order = Order.objects.create(
            order_id=order_id,
            amount=amount,
            status='pending'
        )

        # Prepare payment payload
        payload = {
            'public_key': PUBLIC_KEY,
            'amount': amount,
            'currency': 'AZN',
            'language': 'az',  # or 'en', 'ru' depending on user preference
            'order_id': order_id,
            'description': 'Payment for Job Posting Package',
            'success_redirect_url': 'https://eploy.io/success',
            'error_redirect_url': 'https://eploy.io/error',
        }

        # Encode payload to Base64
        data = base64.b64encode(json.dumps(payload).encode()).decode()

        # Create signature by hashing with sha1 and base64 encoding
        signature_string = f"{PRIVATE_KEY}{data}{PRIVATE_KEY}"
        signature = base64.b64encode(hashlib.sha1(signature_string.encode()).digest()).decode()

        # Send payment request to Epoint
        response = requests.post(EPOINT_API_URL, data={'data': data, 'signature': signature})

        # Check response from Epoint
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                # Redirect to Epoint's payment page
                return redirect(result['redirect_url'])
            else:
                return redirect('payment_error')
        else:
            return redirect('payment_error')

    # Render the payment form template
    return render(request, 'payments/payment_form.html')

def payment_success(request):
    return render(request, 'payments/payment_success.html')

def payment_error(request):
    return render(request, 'payments/payment_error.html')

def handle_result(request):
    if request.method == 'POST':
        data = request.POST.get('data')
        signature = request.POST.get('signature')

        # Recompute the signature for security
        signature_string = f"{PRIVATE_KEY}{data}{PRIVATE_KEY}"
        computed_signature = base64.b64encode(hashlib.sha1(signature_string.encode()).digest()).decode()

        # Validate the signature
        if signature != computed_signature:
            return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)

        # Decode the data
        decoded_data = json.loads(base64.b64decode(data))

        # Process payment result
        order_id = decoded_data.get('order_id')
        status = decoded_data.get('status')

        # Update your database with payment result (Success or Failure)
        order = Order.objects.filter(order_id=order_id).first()
        if order:
            if status == 'success':
                order.status = 'paid'
            else:
                order.status = 'failed'
            order.save()

        return JsonResponse({'status': 'received'}, status=200)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)