"""
M-Pesa STK Push Integration for Olivian Group
"""
import base64
import requests
from datetime import datetime
from django.conf import settings
from decimal import Decimal
import json


class MPesaSTKPush:
    def __init__(self):
        self.environment = getattr(settings, 'MPESA_ENVIRONMENT', 'sandbox')
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.shortcode = getattr(settings, 'MPESA_SHORTCODE', '174379')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')
        
        # URLs based on environment
        if self.environment == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'
            
        self.access_token_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        self.stk_push_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
    
    def get_access_token(self):
        """Get M-Pesa access token"""
        try:
            # Check if credentials are configured
            if not self.consumer_key or not self.consumer_secret:
                print(f"M-Pesa credentials not configured. Consumer key: {'SET' if self.consumer_key else 'NOT SET'}, Consumer secret: {'SET' if self.consumer_secret else 'NOT SET'}")
                return None
            
            # Create credentials string
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            print(f"Using credentials: {self.consumer_key}:{self.consumer_secret[:5]}...")
            print(f"Encoded credentials: {encoded_credentials[:20]}...")
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/json',
                'cache-control': 'no-cache'
            }
            
            print(f"Headers: {headers}")
            print(f"Requesting access token from: {self.access_token_url}")
            
            # Add timeout and disable SSL verification for sandbox
            response = requests.get(
                self.access_token_url, 
                headers=headers, 
                timeout=30,
                verify=True  # Keep SSL verification on
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
            
            response.raise_for_status()
            
            data = response.json()
            access_token = data.get('access_token')
            
            if access_token:
                print("Access token retrieved successfully")
            else:
                print("No access token in response")
                
            return access_token
            
        except Exception as e:
            print(f"Error getting access token: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            return None
    
    def generate_password(self):
        """Generate password for STK push"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_string.encode()).decode()
        return password, timestamp
    
    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url=None, retry=False):
        """
        Initiate STK Push to customer's phone with retry support

        Args:
            phone_number (str): Customer's phone number (254XXXXXXXXX)
            amount (Decimal/float): Amount to be paid
            account_reference (str): Order number or reference
            transaction_desc (str): Description of the transaction
            callback_url (str): Optional custom callback URL
            retry (bool): Whether this is a retry attempt

        Returns:
            dict: Response from M-Pesa API
        """
        try:
            # Check M-Pesa limits and constraints
            amount_float = float(amount)
            if amount_float < 1.0:
                return {'success': False, 'message': 'Minimum M-Pesa payment is KES 1'}
            elif amount_float > 150000.0:
                return {'success': False, 'message': 'Maximum M-Pesa payment is KES 150,000'}

            # Get access token
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'message': 'Failed to get access token'}

            # Generate password and timestamp
            password, timestamp = self.generate_password()

            # Format phone number (ensure it starts with 254)
            original_phone = phone_number
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+254'):
                phone_number = phone_number[1:]
            elif not phone_number.startswith('254'):
                phone_number = '254' + phone_number

            # Validate phone number format
            if not phone_number.isdigit() or len(phone_number) != 12 or not phone_number.startswith('254'):
                return {'success': False, 'message': 'Invalid phone number format'}

            # Convert amount to integer (M-Pesa doesn't accept decimals)
            amount_int = int(amount_float)

            # Determine callback URL
            if not callback_url:
                callback_url = f"{getattr(settings, 'SITE_URL', 'https://olivian.co.ke')}/shop/mpesa/callback/"
                # Use POS callback for POS transactions
                if account_reference.startswith('POS-') or account_reference.startswith('OG-SALE'):
                    callback_url = f"{getattr(settings, 'SITE_URL', 'https://olivian.co.ke')}/pos/api/mpesa/callback/"

            # Prepare request payload
            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount_int,
                "PartyA": phone_number,
                "PartyB": self.shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc[:20]  # Limit description length
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            if retry:
                print(f"Retrying STK Push to: {self.stk_push_url}")
            else:
                print(f"Initiating STK Push to: {self.stk_push_url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")

            response = requests.post(
                self.stk_push_url,
                json=payload,
                headers=headers,
                timeout=30,
                verify=True
            )

            print(f"STK Push Response status: {response.status_code}")
            print(f"STK Push Response content: {response.text}")

            response.raise_for_status()

            data = response.json()

            if data.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'checkout_request_id': data.get('CheckoutRequestID'),
                    'merchant_request_id': data.get('MerchantRequestID'),
                    'response_code': data.get('ResponseCode'),
                    'response_description': data.get('ResponseDescription'),
                    'customer_message': data.get('CustomerMessage')
                }
            else:
                error_message = data.get('ResponseDescription', 'STK Push failed')
                error_code = data.get('ResponseCode')

                print(f"STK Push failed with error {error_code}: {error_message}")

                # Check for retryable errors (network issues, temporary failures)
                retryable_errors = ['1', '24', '25']  # General failures that might be temporary
                if error_code in retryable_errors and not retry:
                    print("Retrying STK Push after a short delay...")
                    import time
                    time.sleep(2)  # Brief delay before retry
                    return self.initiate_stk_push(phone_number=original_phone, amount=amount,
                                                 account_reference=account_reference,
                                                 transaction_desc=transaction_desc,
                                                 callback_url=callback_url, retry=True)

                return {
                    'success': False,
                    'message': error_message,
                    'error_code': error_code
                }

        except requests.exceptions.Timeout:
            if not retry:
                print("STK Push timed out, retrying...")
                import time
                time.sleep(2)
                return self.initiate_stk_push(phone_number=original_phone, amount=amount,
                                             account_reference=account_reference,
                                             transaction_desc=transaction_desc,
                                             callback_url=callback_url, retry=True)
            return {
                'success': False,
                'message': 'Network timeout - please check your connection and try again'
            }

        except requests.exceptions.RequestException as e:
            print(f"Network error in STK Push: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Error response content: {e.response.text}")
            return {
                'success': False,
                'message': f'Network error: {str(e)}'
            }
        except Exception as e:
            print(f"Unexpected error in STK Push: {str(e)}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            }
    
    def query_stk_status(self, checkout_request_id):
        """
        Query the status of an STK Push transaction
        
        Args:
            checkout_request_id (str): CheckoutRequestID from STK Push initiation
            
        Returns:
            dict: Transaction status response
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'message': 'Failed to get access token'}
            
            password, timestamp = self.generate_password()
            
            query_url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            
            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(query_url, json=payload, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Query failed: {str(e)}'
            }


class MPesaCallback:
    """Handle M-Pesa callback responses"""
    
    @staticmethod
    def parse_callback_data(callback_data):
        """
        Parse M-Pesa callback data
        
        Args:
            callback_data (dict): Raw callback data from M-Pesa
            
        Returns:
            dict: Parsed transaction data
        """
        try:
            body = callback_data.get('Body', {})
            stk_callback = body.get('stkCallback', {})
            
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc', '')
            merchant_request_id = stk_callback.get('MerchantRequestID')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            
            transaction_data = {
                'merchant_request_id': merchant_request_id,
                'checkout_request_id': checkout_request_id,
                'result_code': result_code,
                'result_description': result_desc,
                'success': result_code == 0
            }
            
            # If successful, extract metadata
            if result_code == 0:
                callback_metadata = stk_callback.get('CallbackMetadata', {})
                items = callback_metadata.get('Item', [])
                
                for item in items:
                    name = item.get('Name', '')
                    value = item.get('Value')
                    
                    if name == 'Amount':
                        transaction_data['amount'] = value
                    elif name == 'MpesaReceiptNumber':
                        transaction_data['mpesa_receipt_number'] = value
                    elif name == 'TransactionDate':
                        transaction_data['transaction_date'] = value
                    elif name == 'PhoneNumber':
                        transaction_data['phone_number'] = value
            
            return transaction_data
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to parse callback: {str(e)}'
            }
