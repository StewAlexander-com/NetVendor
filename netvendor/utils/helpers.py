"""
Helper functions for NetVendor package.
"""

def get_format_type(first_line: str) -> str:
    """
    Determine the format type of the input file based on its first line.
    
    Args:
        first_line: The first line of the input file
        
    Returns:
        str: The format type ('arp', 'cisco', 'hp', or 'generic')
    """
    if "Internet" in first_line:
        return "arp"
    elif "Vlan" in first_line and "Mac Address" in first_line:
        return "cisco"
    elif "VLAN ID" in first_line and "MAC Address" in first_line:
        return "hp"
    return "generic" 