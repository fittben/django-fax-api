"""
Telnyx API Integration for DID Management
Purchase and manage phone numbers through Telnyx
"""

import requests
import json
from typing import List, Dict, Optional
from django.conf import settings
from .models_complete import DID, Tenant


class TelnyxDIDManager:
    """Manage DIDs through Telnyx API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or getattr(settings, 'TELNYX_API_KEY', '')
        self.base_url = 'https://api.telnyx.com/v2'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def search_available_numbers(self, 
                                area_code: str = None,
                                country: str = 'US',
                                limit: int = 20,
                                features: List[str] = None) -> List[Dict]:
        """
        Search for available phone numbers
        
        Args:
            area_code: 3-digit area code (e.g., '212' for New York)
            country: Country ISO code
            limit: Number of results to return
            features: List of required features ['fax', 'voice', 'sms']
        
        Returns:
            List of available numbers with details
        """
        endpoint = f"{self.base_url}/available_phone_numbers"
        
        params = {
            'filter[country_iso]': country,
            'filter[limit]': limit,
            'filter[features]': features or ['fax', 'voice']
        }
        
        if area_code:
            params['filter[national_destination_code]'] = area_code
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            numbers = []
            
            for number_data in data.get('data', []):
                numbers.append({
                    'phone_number': number_data['phone_number'],
                    'formatted': self._format_number(number_data['phone_number']),
                    'monthly_cost': number_data['cost_information']['monthly_cost'],
                    'upfront_cost': number_data['cost_information']['upfront_cost'],
                    'currency': number_data['cost_information']['currency'],
                    'features': number_data['features'],
                    'region': number_data.get('region_information', {}).get('region_name', ''),
                    'city': number_data.get('region_information', {}).get('city', ''),
                    'state': number_data.get('region_information', {}).get('state', ''),
                })
            
            return numbers
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching numbers: {e}")
            return []
    
    def purchase_number(self, phone_number: str, tenant: Tenant, 
                       messaging_profile_id: str = None,
                       connection_id: str = None) -> Optional[DID]:
        """
        Purchase a phone number from Telnyx
        
        Args:
            phone_number: The phone number to purchase (E.164 format)
            tenant: The tenant to assign the number to
            messaging_profile_id: Optional messaging profile for SMS
            connection_id: Optional connection for voice/fax
        
        Returns:
            DID object if successful, None otherwise
        """
        endpoint = f"{self.base_url}/number_orders"
        
        payload = {
            'phone_numbers': [{'phone_number': phone_number}]
        }
        
        if messaging_profile_id:
            payload['messaging_profile_id'] = messaging_profile_id
        
        if connection_id:
            payload['connection_id'] = connection_id
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            order_id = data['data']['id']
            
            # Wait for order to complete and get phone number ID
            number_id = self._wait_for_order(order_id)
            
            if number_id:
                # Create DID record
                did = DID.objects.create(
                    number=self._clean_number(phone_number),
                    tenant=tenant,
                    provider='telnyx',
                    provider_sid=number_id,
                    is_fax_enabled=True,
                    is_voice_enabled=True,
                    is_active=True,
                    description=f"Purchased from Telnyx"
                )
                
                # Configure the number for fax
                self.configure_for_fax(number_id, connection_id)
                
                return did
            
        except requests.exceptions.RequestException as e:
            print(f"Error purchasing number: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
        
        return None
    
    def configure_for_fax(self, phone_number_id: str, connection_id: str = None):
        """
        Configure a Telnyx number for fax reception
        
        Args:
            phone_number_id: Telnyx phone number ID
            connection_id: Connection ID for routing
        """
        endpoint = f"{self.base_url}/phone_numbers/{phone_number_id}"
        
        # Get or create fax connection
        if not connection_id:
            connection_id = self.get_or_create_fax_connection()
        
        payload = {
            'connection_id': connection_id,
            'tags': ['fax', 'production'],
            'external_pin': None  # Remove PIN for fax
        }
        
        try:
            response = requests.patch(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            print(f"Number configured for fax: {phone_number_id}")
            
        except requests.exceptions.RequestException as e:
            print(f"Error configuring number: {e}")
    
    def get_or_create_fax_connection(self) -> Optional[str]:
        """
        Get existing fax connection or create a new one
        
        Returns:
            Connection ID
        """
        endpoint = f"{self.base_url}/fax_applications"
        
        # Check for existing fax application
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data['data']:
                return data['data'][0]['id']
            
            # Create new fax application
            payload = {
                'application_name': 'Django Fax Service',
                'webhook_event_url': f"{settings.SITE_URL}/api/fax/webhook/telnyx/",
                'webhook_event_failover_url': f"{settings.SITE_URL}/api/fax/webhook/telnyx/failover/",
                'inbound': {
                    'sip_subdomain': 'fax',
                    'sip_subdomain_receive_settings': 'only_my_connections'
                },
                'outbound': {
                    'outbound_voice_profile_id': None
                }
            }
            
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            
            return response.json()['data']['id']
            
        except requests.exceptions.RequestException as e:
            print(f"Error managing fax connection: {e}")
            return None
    
    def release_number(self, phone_number: str) -> bool:
        """
        Release a phone number back to Telnyx
        
        Args:
            phone_number: The phone number to release
        
        Returns:
            True if successful
        """
        # First, find the phone number ID
        number_id = self._get_number_id(phone_number)
        
        if not number_id:
            return False
        
        endpoint = f"{self.base_url}/phone_numbers/{number_id}"
        
        try:
            response = requests.delete(endpoint, headers=self.headers)
            response.raise_for_status()
            
            # Update DID record
            try:
                did = DID.objects.get(number=self._clean_number(phone_number))
                did.is_active = False
                did.save()
            except DID.DoesNotExist:
                pass
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Error releasing number: {e}")
            return False
    
    def get_number_details(self, phone_number: str) -> Optional[Dict]:
        """
        Get details about a phone number
        
        Args:
            phone_number: The phone number to query
        
        Returns:
            Dictionary with number details
        """
        number_id = self._get_number_id(phone_number)
        
        if not number_id:
            return None
        
        endpoint = f"{self.base_url}/phone_numbers/{number_id}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()['data']
            
            return {
                'id': data['id'],
                'phone_number': data['phone_number'],
                'status': data['status'],
                'connection_id': data.get('connection_id'),
                'messaging_profile_id': data.get('messaging_profile_id'),
                'tags': data.get('tags', []),
                'created_at': data['created_at'],
                'billing_group_id': data.get('billing_group_id')
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting number details: {e}")
            return None
    
    def send_fax(self, from_number: str, to_number: str, 
                media_url: str, connection_id: str = None) -> Optional[str]:
        """
        Send a fax through Telnyx API
        
        Args:
            from_number: Sender's phone number (must be a Telnyx number)
            to_number: Recipient's phone number
            media_url: URL of the document to fax (PDF or TIFF)
            connection_id: Optional connection ID
        
        Returns:
            Fax ID if successful
        """
        endpoint = f"{self.base_url}/faxes"
        
        # Ensure numbers are in E.164 format
        if not from_number.startswith('+'):
            from_number = f"+1{from_number}" if len(from_number) == 10 else f"+{from_number}"
        
        if not to_number.startswith('+'):
            to_number = f"+1{to_number}" if len(to_number) == 10 else f"+{to_number}"
        
        payload = {
            'from': from_number,
            'to': to_number,
            'media_url': media_url,
            'connection_id': connection_id or self.get_or_create_fax_connection()
        }
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data['data']['id']
            
        except requests.exceptions.RequestException as e:
            print(f"Error sending fax: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
            return None
    
    def get_fax_status(self, fax_id: str) -> Optional[Dict]:
        """
        Get the status of a fax transmission
        
        Args:
            fax_id: Telnyx fax ID
        
        Returns:
            Dictionary with fax status
        """
        endpoint = f"{self.base_url}/faxes/{fax_id}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()['data']
            
            return {
                'id': data['id'],
                'status': data['status'],
                'from': data['from'],
                'to': data['to'],
                'pages': data.get('page_count'),
                'created_at': data['created_at'],
                'completed_at': data.get('completed_at'),
                'failure_reason': data.get('failure_reason')
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting fax status: {e}")
            return None
    
    def _format_number(self, phone_number: str) -> str:
        """Format phone number for display"""
        # Remove country code if present
        if phone_number.startswith('+1'):
            phone_number = phone_number[2:]
        elif phone_number.startswith('1') and len(phone_number) == 11:
            phone_number = phone_number[1:]
        
        # Format as (XXX) XXX-XXXX
        if len(phone_number) == 10:
            return f"({phone_number[:3]}) {phone_number[3:6]}-{phone_number[6:]}"
        
        return phone_number
    
    def _clean_number(self, phone_number: str) -> str:
        """Clean phone number to 10 digits"""
        # Remove all non-digits
        cleaned = ''.join(filter(str.isdigit, phone_number))
        
        # Remove country code if present
        if cleaned.startswith('1') and len(cleaned) == 11:
            cleaned = cleaned[1:]
        
        return cleaned
    
    def _get_number_id(self, phone_number: str) -> Optional[str]:
        """Get Telnyx ID for a phone number"""
        endpoint = f"{self.base_url}/phone_numbers"
        
        params = {
            'filter[phone_number]': phone_number
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data['data']:
                return data['data'][0]['id']
            
        except requests.exceptions.RequestException:
            pass
        
        return None
    
    def _wait_for_order(self, order_id: str, max_attempts: int = 10) -> Optional[str]:
        """Wait for number order to complete"""
        import time
        
        endpoint = f"{self.base_url}/number_orders/{order_id}"
        
        for _ in range(max_attempts):
            try:
                response = requests.get(endpoint, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()['data']
                
                if data['status'] == 'success':
                    # Get the phone number ID
                    if data['phone_numbers']:
                        return data['phone_numbers'][0]['id']
                elif data['status'] == 'failed':
                    print(f"Order failed: {data.get('failure_reason')}")
                    return None
                
                time.sleep(2)
                
            except requests.exceptions.RequestException:
                pass
        
        return None