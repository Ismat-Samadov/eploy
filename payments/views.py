import os
import json
import base64
import hashlib
from uuid import uuid4
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
import requests
from dotenv import load_dotenv
from jobs.models import JobPost
from .models import Order
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import logging
from django.urls import reverse
from django.contrib import messages

logger = logging.getLogger(__name__)

# Load .env file to access sensitive data
load_dotenv()

PUBLIC_KEY = os.getenv('PUBLIC_KEY')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
EPOINT_API_URL = 'https://epoint.az/api/1/request'

def initiate_payment(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, posted_by=request.user)

    # Check if the job is already paid
    if job.is_paid:
        messages.success(request, 'This job is already paid.')
        return redirect('job_list')

    # Create a new order for the payment
    amount = 20.00  # You can make this dynamic based on your business logic
    order = Order.objects.create(
        order_id=str(uuid4()),
        amount=amount,
        status='pending',
        job=job  # Associate the job with the order
    )

    payload = {
        'public_key': PUBLIC_KEY,
        'amount': str(order.amount),
        'currency': 'AZN',
        'language': 'az',
        'order_id': order.order_id,
        'description': 'Payment for Job Posting',
        'success_redirect_url': request.build_absolute_uri(reverse('payment_success') + f'?order_id={order.order_id}'),
        'error_redirect_url': request.build_absolute_uri(reverse('payment_error')),
    }

    # Encode payload to Base64
    data = base64.b64encode(json.dumps(payload).encode()).decode()

    # Generate signature using private_key and payload
    signature_string = f"{PRIVATE_KEY}{data}{PRIVATE_KEY}"
    signature = base64.b64encode(hashlib.sha1(signature_string.encode()).digest()).decode()

    # Send the request to Epoint
    response = requests.post(EPOINT_API_URL, data={'data': data, 'signature': signature})

    if response.status_code == 200:
        result = response.json()
        if result.get('status') == 'success':
            return redirect(result['redirect_url'])  # Redirect user to payment page
        else:
            return redirect('/payments/error/')
    else:
        return redirect('/payments/error/')


def create_payment(request, order_id):
    # Retrieve the order based on the order_id
    order = get_object_or_404(Order, order_id=order_id)

    # Define payment details and order info
    amount = order.amount

    # Prepare payload for payment
    payload = {
        'public_key': PUBLIC_KEY,
        'amount': str(amount),
        'currency': 'AZN',
        'language': 'az',
        'order_id': order_id,
        'description': 'Payment for Job Posting',
        'success_redirect_url': request.build_absolute_uri('/payments/success/'),
        'error_redirect_url': request.build_absolute_uri('/payments/error/'),
    }

    # Encode payload and generate signature
    data = base64.b64encode(json.dumps(payload).encode()).decode()
    signature_string = f"{PRIVATE_KEY}{data}{PRIVATE_KEY}"
    signature = base64.b64encode(hashlib.sha1(signature_string.encode()).digest()).decode()

    # Send the request to the payment API
    response = requests.post(EPOINT_API_URL, data={'data': data, 'signature': signature})

    # Handle response
    if response.status_code == 200:
        result = response.json()
        if result.get('status') == 'success':
            return redirect(result['redirect_url'])
        else:
            return redirect('/payments/error/')
    else:
        return redirect('/payments/error/')


def payment_success(request):
    logger.info(f'Payment success called with query params: {request.GET}')
    
    # Get the order_id from the query string
    order_id = request.GET.get('order_id')

    if not order_id:
        logger.error('No order ID provided')
        return redirect('/payments/error/')

    # Find the order with the given order_id
    order = Order.objects.filter(order_id=order_id).first()

    if not order:
        logger.error(f'Order with ID {order_id} not found')
        return redirect('/payments/error/')

    # Mark the order as paid if it's still pending
    if order.status == 'pending':
        order.status = 'paid'
        order.save()

        # If the order is linked to a job, mark the job as paid
        if order.job:
            job = order.job
            job.is_paid = True
            job.save()

        return render(request, 'payments/payments_success.html', {'job': job})
    
    return redirect('/payments/error/')


def payment_error(request):
    order_id = request.GET.get('order_id')
    order = Order.objects.filter(order_id=order_id).first()

    if order:
        # Mark the job as deleted if payment fails
        job = order.job
        job.deleted = True  # Mark as deleted
        job.save()

    return render(request, 'payments/payment_error.html')


@csrf_exempt
def handle_epoint_result(request):
    if request.method == 'POST':
        data = request.POST.get('data')
        signature = request.POST.get('signature')

        logger.debug(f"Received payment data: {data}, signature: {signature}")

        # Recompute the signature
        signature_string = f"{PRIVATE_KEY}{data}{PRIVATE_KEY}"
        computed_signature = base64.b64encode(hashlib.sha1(signature_string.encode()).digest()).decode()

        logger.debug(f"Computed signature: {computed_signature}")

        # Verify the signature
        if signature != computed_signature:
            logger.error("Invalid signature detected.")
            return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)

        # Decode data and process payment result
        decoded_data = json.loads(base64.b64decode(data))
        logger.debug(f"Decoded payment data: {decoded_data}")

        order_id = decoded_data.get('order_id')
        status = decoded_data.get('status')
        logger.debug(f"Order ID: {order_id}, Status: {status}")

        # Update the order based on the status received
        order = Order.objects.filter(order_id=order_id).first()
        if order:
            if status == 'success':
                logger.info(f"Payment successful for order {order_id}.")
                order.status = 'paid'  # Update status to 'paid'
                job = order.job
                job.is_paid = True  # Mark the job as paid
                job.save()
            else:
                logger.warning(f"Payment failed for order {order_id}.")
                order.status = 'failed'
            order.save()

        return JsonResponse({'status': 'received'}, status=200)

    logger.error("Invalid request method.")
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
