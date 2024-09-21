import os
import json
import base64
import hashlib
from uuid import uuid4
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
import requests
from dotenv import load_dotenv
from jobs.models import JobPost  # Assuming JobPost is in jobs app
from .models import Order
from django.conf import settings

# Load .env file to access sensitive data
load_dotenv()

PUBLIC_KEY = os.getenv('PUBLIC_KEY')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
EPOINT_API_URL = 'https://epoint.az/api/1/request'


def initiate_payment(request, job_id):
    # Get the job that needs payment
    job = get_object_or_404(JobPost, id=job_id)

    # Check if the job is already paid
    if job.is_paid:
        return redirect('job_list')  # Redirect if already paid

    # Define posting cost (could be dynamic)
    amount = 20.00  # Example cost, adjust as needed

    # Create an order for the job post
    order_id = str(uuid4())
    order = Order.objects.create(
        order_id=order_id,
        amount=amount,
        status='pending',
        job=job  # Link to the job
    )

    # Prepare payment payload
    payload = {
        'public_key': PUBLIC_KEY,
        'amount': str(order.amount),
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

    # Send the request to Epoint
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
    order_id = request.GET.get('order_id')
    if order_id:
        order = Order.objects.filter(order_id=order_id).first()
        if order and order.status == 'pending':
            # Mark the order and job as paid
            order.status = 'paid'
            order.save()

            job = order.job
            job.is_paid = True
            job.save()

            return render(request, 'payments/payment_success.html', {'job': job})
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


def handle_epoint_result(request):
    if request.method == 'POST':
        data = request.POST.get('data')
        signature = request.POST.get('signature')

        # Recompute the signature
        signature_string = f"{PRIVATE_KEY}{data}{PRIVATE_KEY}"
        computed_signature = base64.b64encode(hashlib.sha1(signature_string.encode()).digest()).decode()

        # Verify the signature
        if signature != computed_signature:
            return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)

        # Decode data and process payment result
        decoded_data = json.loads(base64.b64decode(data))
        order_id = decoded_data.get('order_id')
        status = decoded_data.get('status')

        order = Order.objects.filter(order_id=order_id).first()
        if order:
            if status == 'success':
                order.status = 'paid'
                job = order.job
                job.is_paid = True
                job.save()
            else:
                order.status = 'failed'
            order.save()

        return JsonResponse({'status': 'received'}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
