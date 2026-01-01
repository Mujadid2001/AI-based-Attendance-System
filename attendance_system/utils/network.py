"""
Network utility functions for dynamic IP detection and QR code generation.

Provides cross-platform network IP detection for ensuring QR codes and external
device connections work across development, production, and Docker environments.
"""
import socket
import platform
import logging
import subprocess
import re
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


def is_wsl() -> bool:
    """
    Detect if running inside Windows Subsystem for Linux.
    
    Returns:
        bool: True if running in WSL, False otherwise
    """
    try:
        # Check for WSL in /proc/version
        with open('/proc/version', 'r') as f:
            version_info = f.read().lower()
            if 'microsoft' in version_info or 'wsl' in version_info:
                return True
    except:
        pass
    return False


def get_windows_host_ip() -> Optional[str]:
    """
    Get the Windows host's LAN IP when running in WSL.
    
    WSL2 uses a virtualized network, so we need to get the actual
    Windows host IP that other devices on the LAN can reach.
    
    Returns:
        str: Windows host LAN IP or None if detection fails
    """
    try:
        # Method 1: Get Windows host IP via nameserver in /etc/resolv.conf
        # This gives us the Windows host's IP on the WSL-Windows bridge
        with open('/etc/resolv.conf', 'r') as f:
            for line in f:
                if line.startswith('nameserver'):
                    wsl_host_ip = line.split()[1]
                    logger.info(f"WSL detected - Windows host bridge IP: {wsl_host_ip}")
                    
                    # Now we need to get the Windows host's actual LAN IP
                    # Use PowerShell through wsl.exe to query Windows network
                    try:
                        # Get Windows LAN IP using PowerShell
                        cmd = [
                            'powershell.exe', '-Command',
                            '(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias (Get-NetRoute -DestinationPrefix "0.0.0.0/0").InterfaceAlias | Where-Object {$_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*"} | Select-Object -First 1).IPAddress'
                        ]
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                        if result.returncode == 0 and result.stdout.strip():
                            windows_lan_ip = result.stdout.strip()
                            logger.info(f"WSL: Detected Windows host LAN IP: {windows_lan_ip}")
                            return windows_lan_ip
                    except Exception as e:
                        logger.warning(f"Failed to get Windows LAN IP via PowerShell: {e}")
                    
                    # Fallback: Try alternative PowerShell command
                    try:
                        cmd = [
                            'powershell.exe', '-Command',
                            'Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or ($_.IPAddress -like "172.*" -and [int]($_.IPAddress.Split(".")[1]) -ge 16 -and [int]($_.IPAddress.Split(".")[1]) -le 31)} | Select-Object -First 1 -ExpandProperty IPAddress'
                        ]
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                        if result.returncode == 0 and result.stdout.strip():
                            windows_lan_ip = result.stdout.strip()
                            logger.info(f"WSL: Detected Windows host LAN IP (fallback): {windows_lan_ip}")
                            return windows_lan_ip
                    except Exception as e:
                        logger.warning(f"Failed to get Windows LAN IP via PowerShell (fallback): {e}")
                    
                    break
    except Exception as e:
        logger.warning(f"Error detecting Windows host IP in WSL: {e}")
    
    return None


def get_local_network_ip() -> Optional[str]:
    """
    Detect the local network IP address that other devices can reach.
    
    Works cross-platform (Windows/Linux/macOS) and handles multiple interfaces.
    Returns the first non-localhost IP that's reachable on the local network.
    
    Special handling for WSL (Windows Subsystem for Linux):
    - Detects WSL environment and gets Windows host's actual LAN IP
    - This ensures mobile devices can reach the server
    
    Uses multiple detection methods with fallback:
    1. WSL detection - Get Windows host IP (if running in WSL)
    2. Socket routing to external DNS (most reliable)
    3. Hostname resolution
    4. Network interface enumeration (requires netifaces)
    
    Returns:
        str: IP address (e.g., '192.168.1.100') or None if detection fails
    """
    # Special case: WSL detection (must be first)
    if is_wsl():
        logger.info("Running in WSL - attempting to get Windows host LAN IP")
        windows_ip = get_windows_host_ip()
        if windows_ip and not windows_ip.startswith('127.') and not windows_ip.startswith('169.254.'):
            logger.info(f"WSL: Using Windows host LAN IP for network accessibility: {windows_ip}")
            return windows_ip
        else:
            logger.warning("WSL: Could not detect Windows host LAN IP - falling back to WSL IP (may not be accessible from mobile)")
    
    try:
        # Method 1: Connect to external host (doesn't actually send data)
        # This finds the interface that would be used for internet traffic
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Use Google's public DNS as target (8.8.8.8:80)
            # This works even without internet - just checks routing table
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
            
            # Validate it's not localhost
            if local_ip and not local_ip.startswith('127.'):
                logger.info(f"Detected local network IP via routing: {local_ip}")
                return local_ip
    except Exception as e:
        logger.warning(f"Network detection method 1 (routing) failed: {e}")
    
    try:
        # Method 2: Get hostname and resolve it
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        if local_ip and not local_ip.startswith('127.'):
            logger.info(f"Detected local network IP via hostname: {local_ip}")
            return local_ip
    except Exception as e:
        logger.warning(f"Network detection method 2 (hostname) failed: {e}")
    
    try:
        # Method 3: Enumerate all interfaces (more comprehensive)
        import netifaces
        
        # Get all network interfaces
        interfaces = netifaces.interfaces()
        
        for interface in interfaces:
            # Skip VPN interfaces (warn if detected)
            if any(vpn in interface.lower() for vpn in ['tun', 'tap', 'vpn']):
                logger.warning(f"VPN interface detected ({interface}) - may need manual SERVER_BASE_URL override")
                continue
            
            # Get addresses for this interface
            addrs = netifaces.ifaddresses(interface)
            
            # Look for IPv4 addresses
            if netifaces.AF_INET in addrs:
                for addr_info in addrs[netifaces.AF_INET]:
                    ip = addr_info.get('addr')
                    
                    # Skip localhost and link-local addresses (APIPA)
                    if ip and not ip.startswith('127.') and not ip.startswith('169.254.'):
                        # Prefer private network ranges (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
                        if ip.startswith('192.168.'):
                            logger.info(f"Detected local network IP via interface {interface}: {ip} (192.168.x.x range)")
                            return ip
                        elif ip.startswith('10.'):
                            logger.info(f"Detected local network IP via interface {interface}: {ip} (10.x.x.x range)")
                            return ip
                        elif ip.startswith('172.'):
                            second_octet = int(ip.split('.')[1])
                            if 16 <= second_octet <= 31:
                                logger.info(f"Detected local network IP via interface {interface}: {ip} (172.16-31.x.x range)")
                                return ip
    except ImportError:
        logger.warning("netifaces not installed - install with: pip install netifaces")
    except Exception as e:
        logger.warning(f"Network detection method 3 (netifaces) failed: {e}")
    
    # Fallback to localhost if all methods fail
    logger.error("Could not detect local network IP - falling back to localhost")
    return '127.0.0.1'


def get_server_base_url(request=None, force_detect: bool = False) -> str:
    """
    Get the base URL for the server, with flexible configuration.
    
    Priority system:
    1. Environment variable SERVER_BASE_URL (if set)
    2. Dynamic IP detection (if force_detect=True or in development)
    3. Request-based URL (if request is provided)
    4. Fallback to localhost
    
    Args:
        request: Django request object (optional)
        force_detect: Force dynamic IP detection regardless of settings
    
    Returns:
        str: Full base URL (e.g., 'http://192.168.1.100:8000')
    """
    # Priority 1: Environment variable (production override)
    env_base_url = getattr(settings, 'SERVER_BASE_URL', None)
    if env_base_url and not force_detect:
        logger.info(f"Using SERVER_BASE_URL from settings: {env_base_url}")
        return env_base_url.rstrip('/')
    
    # Priority 2: Dynamic detection (for local network accessibility)
    if force_detect or settings.DEBUG:
        local_ip = get_local_network_ip()
        if local_ip and local_ip != '127.0.0.1':
            # Determine port
            port = getattr(settings, 'SERVER_PORT', '8000')
            
            # Determine scheme
            scheme = 'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'
            
            base_url = f"{scheme}://{local_ip}:{port}"
            logger.info(f"Using dynamically detected base URL: {base_url}")
            return base_url
    
    # Priority 3: Request-based (with caution)
    if request:
        try:
            base_url = request.build_absolute_uri('/').rstrip('/')
            logger.info(f"Using request-based base URL: {base_url}")
            return base_url
        except Exception as e:
            logger.warning(f"Request-based URL detection failed: {e}")
    
    # Priority 4: Fallback
    fallback = 'http://localhost:8000'
    logger.warning(f"All detection methods failed - using fallback: {fallback}")
    return fallback


def get_accessible_ip_info() -> dict:
    """
    Get comprehensive IP information for troubleshooting.
    
    Returns detailed information about detected IPs, network interfaces,
    and platform details. Useful for debugging network connectivity issues.
    
    Returns:
        dict: Contains platform, hostname, local_ip, all_ips, warnings, and wsl_info
    """
    info = {
        'platform': platform.system(),
        'hostname': socket.gethostname(),
        'is_wsl': is_wsl(),
        'local_ip': get_local_network_ip(),
        'all_ips': [],
        'warnings': []
    }
    
    # Add WSL-specific information
    if info['is_wsl']:
        info['wsl_info'] = {
            'detected': True,
            'windows_host_ip': get_windows_host_ip(),
            'note': 'Running in WSL - using Windows host IP for LAN accessibility'
        }
        info['warnings'].append('Running in WSL2 - mobile devices must connect to Windows host IP, not WSL internal IP')
    
    # Try to get all network interfaces
    try:
        import netifaces
        
        for interface in netifaces.interfaces():
            # Check for VPN
            is_vpn = any(vpn in interface.lower() for vpn in ['tun', 'tap', 'vpn'])
            if is_vpn:
                info['warnings'].append(f"VPN interface detected: {interface}")
            
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr.get('addr')
                    # Categorize IP type
                    ip_type = 'unknown'
                    if ip.startswith('127.'):
                        ip_type = 'localhost'
                    elif ip.startswith('169.254.'):
                        ip_type = 'link-local (APIPA)'
                    elif ip.startswith('192.168.'):
                        ip_type = 'private (Class C)'
                    elif ip.startswith('10.'):
                        ip_type = 'private (Class A)'
                    elif ip.startswith('172.'):
                        second_octet = int(ip.split('.')[1])
                        if 16 <= second_octet <= 31:
                            ip_type = 'private (Class B)'
                        else:
                            ip_type = 'public'
                    else:
                        ip_type = 'public'
                    
                    info['all_ips'].append({
                        'interface': interface,
                        'ip': ip,
                        'netmask': addr.get('netmask'),
                        'type': ip_type,
                        'is_vpn': is_vpn
                    })
    except ImportError:
        info['warnings'].append("netifaces not installed - limited interface information available")
    except Exception as e:
        info['warnings'].append(f"Error enumerating interfaces: {str(e)}")
    
    return info
