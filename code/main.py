import requests
import OpenSSL.crypto
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context
import ssl
import tempfile
import os
from typing import Optional, Union, Dict, Any

class PFXAdapter(HTTPAdapter):
    def __init__(self, 
                 pfx_path: str, 
                 pfx_password: str, 
                 verify: bool = True, 
                 *args: Any, 
                 **kwargs: Any):
        """
        Initialize PFX adapter for certificate-based authentication
        
        Args:
            pfx_path: Path to the PFX certificate file
            pfx_password: Password for the PFX certificate
            verify: Whether to verify SSL certificates
            *args: Additional positional arguments for HTTPAdapter
            **kwargs: Additional keyword arguments for HTTPAdapter
        """
        self.pfx_path = pfx_path
        self.pfx_password = pfx_password
        self.verify = verify
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args: Any, **kwargs: Any):
        context = create_urllib3_context()
        try:
            # Load PFX certificate
            with open(self.pfx_path, 'rb') as pfx_file:
                pfx_data = pfx_file.read()
            
            # Convert PFX to PEM format
            p12 = OpenSSL.crypto.load_pkcs12(pfx_data, self.pfx_password)
            
            # Create temporary files for cert and key
            with tempfile.NamedTemporaryFile(delete=False) as cert_temp:
                cert_temp.write(OpenSSL.crypto.dump_certificate(
                    OpenSSL.crypto.FILETYPE_PEM, 
                    p12.get_certificate()
                ))
                cert_path = cert_temp.name
            
            with tempfile.NamedTemporaryFile(delete=False) as key_temp:
                key_temp.write(OpenSSL.crypto.dump_privatekey(
                    OpenSSL.crypto.FILETYPE_PEM, 
                    p12.get_privatekey()
                ))
                key_path = key_temp.name
            
            try:
                context.load_cert_chain(
                    certfile=cert_path,
                    keyfile=key_path
                )
            finally:
                # Clean up temporary files
                os.unlink(cert_path)
                os.unlink(key_path)
            
            if not self.verify:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            
        except Exception as e:
            raise RuntimeError(f"Failed to load PFX certificate: {str(e)}")
        
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

def create_secure_session(
    pfx_path: str, 
    pfx_password: str, 
    base_url: str,
    verify: bool = True,
    headers: Optional[Dict[str, str]] = None
) -> requests.Session:
    """
    Create a session with PFX certificate authentication
    
    Args:
        pfx_path: Path to the PFX certificate file
        pfx_password: Password for the PFX certificate
        base_url: Base URL of the server
        verify: Whether to verify SSL certificates
        headers: Optional headers to include in all requests
        
    Returns:
        requests.Session: Configured session object
        
    Raises:
        RuntimeError: If session creation fails
    """
    try:
        session = requests.Session()
        adapter = PFXAdapter(pfx_path, pfx_password, verify=verify)
        session.mount(base_url, adapter)
        
        if headers:
            session.headers.update(headers)
        
        return session
    except Exception as e:
        raise RuntimeError(f"Failed to create secure session: {str(e)}")

def test_connection(
    session: requests.Session, 
    url: str,
    timeout: int = 30,
    expected_status: Union[int, range] = range(200, 300)
) -> bool:
    """
    Test the secure connection
    
    Args:
        session: Configured session object
        url: URL to test
        timeout: Request timeout in seconds
        expected_status: Expected HTTP status code or range
        
    Returns:
        bool: True if connection is successful
        
    Note:
        A successful connection means:
        1. Request completes without errors
        2. SSL handshake is successful
        3. Response status code matches expected_status
    """
    try:
        response = session.get(url, timeout=timeout)
        
        if isinstance(expected_status, range):
            status_ok = response.status_code in expected_status
        else:
            status_ok = response.status_code == expected_status
            
        if status_ok:
            print(f"Connection successful! Status code: {response.status_code}")
            return True
        else:
            print(f"Connection failed: Unexpected status code {response.status_code}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"SSL handshake failed: {str(e)}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Configuration
    PFX_PATH = "path/to/your/certificate.pfx"  # Update with your PFX file path
    PFX_PASSWORD = "your_password"  # Update with your PFX password
    BASE_URL = "https://your.host.com"  # Update with your host URL
    TEST_ENDPOINT = f"{BASE_URL}/test"  # Update with a valid endpoint
    
    # Optional configuration
    CUSTOM_HEADERS = {
        "User-Agent": "CustomSecureClient/1.0",
        # Add any other required headers
    }
    
    try:
        # Create secure session with custom headers
        session = create_secure_session(
            pfx_path=PFX_PATH,
            pfx_password=PFX_PASSWORD,
            base_url=BASE_URL,
            headers=CUSTOM_HEADERS
        )
        
        # Test the connection with a 30-second timeout
        connection_successful = test_connection(
            session=session,
            url=TEST_ENDPOINT,
            timeout=30
        )
        
        if connection_successful:
            print("Ready to make secure requests!")
            
            # Example request with error handling
            try:
                response = session.get(f"{BASE_URL}/your-endpoint")
                data = response.json()
                print("Request successful:", data)
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {str(e)}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
