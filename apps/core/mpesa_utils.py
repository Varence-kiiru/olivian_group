"""
M-Pesa Payment Integration Utilities
Handles STK Push, payment callbacks, and transaction verification
"""

import requests
import base64
import json
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class MPesaAPI:
    """M-Pesa Daraja API Integration"""
    
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.environment = settings.MPESA_ENVIRONMENT
        
        # Set API URLs based on environment
        if self.environment == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'
    
    def get_access_token(self):
        """Get OAuth access token from M-Pesa API"""
        
        # Check if token exists in cache
        token = cache.get('mpesa_access_token')
        if token:
            return token
        
        try:
            # Prepare credentials
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            # Request headers
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/json'
            }
            
            # Make request
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                expires_in = int(token_data.get('expires_in', 3600))
                
                # Cache token (with 5 minute buffer)
                cache.set('mpesa_access_token', access_token, expires_in - 300)
                
                logger.info("M-Pesa access token obtained successfully")
                return access_token
            else:
                logger.error(f"Failed to get M-Pesa access token: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting M-Pesa access token: {str(e)}")
            return None
    
    def generate_password(self, timestamp=None):
        """Generate password for STK Push"""
        if not timestamp:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        password_string = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_string.encode()).decode()
        
        return password, timestamp
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url=None):
        """
        Initiate STK Push payment request
        
        Args:
            phone_number (str): Customer phone number in format 254XXXXXXXXX
            amount (float): Amount to pay
            account_reference (str): Reference for the transaction (e.g., order number)
            transaction_desc (str): Description of the transaction
            callback_url (str): URL to receive payment callback
        
        Returns:
            dict: Response from M-Pesa API
        """
        
        access_token = self.get_access_token()
        if not access_token:
            return {'success': False, 'message': 'Failed to get access token'}
        
        try:
            # Format phone number
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+254'):
                phone_number = phone_number[1:]
            elif not phone_number.startswith('254'):
                phone_number = '254' + phone_number
            
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            # Default callback URL
            if not callback_url:
                callback_url = f"{settings.SITE_URL}/api/mpesa/callback/"
            
            # Request headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Request payload
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(float(amount)),
                'PartyA': phone_number,
                'PartyB': self.shortcode,
                'PhoneNumber': phone_number,
                'CallBackURL': callback_url,
                'AccountReference': account_reference,
                'TransactionDesc': transaction_desc
            }
            
            # Make STK Push request
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get('ResponseCode') == '0':
                    logger.info(f"STK Push initiated successfully for {phone_number}")
                    return {
                        'success': True,
                        'checkout_request_id': response_data.get('CheckoutRequestID'),
                        'merchant_request_id': response_data.get('MerchantRequestID'),
                        'response_code': response_data.get('ResponseCode'),
                        'response_description': response_data.get('ResponseDescription'),
                        'customer_message': response_data.get('CustomerMessage')
                    }
                else:
                    logger.error(f"STK Push failed: {response_data}")
                    return {
                        'success': False,
                        'message': response_data.get('ResponseDescription', 'Payment request failed')
                    }
            else:
                logger.error(f"STK Push request failed: {response.text}")
                return {'success': False, 'message': 'Payment request failed'}
                
        except Exception as e:
            logger.error(f"Error initiating STK Push: {str(e)}")
            return {'success': False, 'message': 'Payment request failed'}
    
    def query_stk_status(self, checkout_request_id):
        """Query STK Push payment status"""
        
        access_token = self.get_access_token()
        if not access_token:
            return {'success': False, 'message': 'Failed to get access token'}
        
        try:
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            # Request headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Request payload
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }
            
            # Make query request
            url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"STK status query successful: {response_data}")
                return {
                    'success': True,
                    'data': response_data
                }
            else:
                logger.error(f"STK status query failed: {response.text}")
                return {'success': False, 'message': 'Status query failed'}
                
        except Exception as e:
            logger.error(f"Error querying STK status: {str(e)}")
            return {'success': False, 'message': 'Status query failed'}
    
    def process_callback(self, callback_data):
        """Process M-Pesa callback data"""
        try:
            body = callback_data.get('Body', {})
            stk_callback = body.get('stkCallback', {})
            
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            merchant_request_id = stk_callback.get('MerchantRequestID')
            
            # Initialize response data
            response_data = {
                'checkout_request_id': checkout_request_id,
                'merchant_request_id': merchant_request_id,
                'result_code': result_code,
                'result_description': result_desc,
                'success': result_code == 0
            }
            
            if result_code == 0:  # Success
                # Extract callback metadata
                callback_metadata = stk_callback.get('CallbackMetadata', {})
                items = callback_metadata.get('Item', [])
                
                for item in items:
                    name = item.get('Name')
                    value = item.get('Value')
                    
                    if name == 'Amount':
                        response_data['amount'] = float(value)
                    elif name == 'MpesaReceiptNumber':
                        response_data['mpesa_receipt_number'] = value
                    elif name == 'TransactionDate':
                        # Convert M-Pesa timestamp to datetime
                        try:
                            transaction_date = datetime.strptime(str(value), '%Y%m%d%H%M%S')
                            response_data['transaction_date'] = transaction_date
                        except:
                            response_data['transaction_date'] = timezone.now()
                    elif name == 'PhoneNumber':
                        response_data['phone_number'] = str(value)
                
                logger.info(f"M-Pesa payment successful: {response_data}")
            else:
                logger.warning(f"M-Pesa payment failed: {result_desc}")
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing M-Pesa callback: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Global M-Pesa API instance
mpesa_api = MPesaAPI()

# Helper functions for common operations
def initiate_payment(phone_number, amount, order_number, description):
    """Helper function to initiate M-Pesa payment"""
    return mpesa_api.stk_push(
        phone_number=phone_number,
        amount=amount,
        account_reference=order_number,
        transaction_desc=description
    )

def check_payment_status(checkout_request_id):
    """Helper function to check payment status"""
    return mpesa_api.query_stk_status(checkout_request_id)

def process_payment_callback(callback_data):
    """Helper function to process payment callback"""
    return mpesa_api.process_callback(callback_data)
