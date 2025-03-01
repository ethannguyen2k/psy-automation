import re

unit_pattern = r'^([\dA-Za-z]+)\/(\d+)(?:\s+(.+))?$'
address = "35B/12 Example Street"

unit_match = re.match(unit_pattern, address)
if unit_match:
    # Extract the main address without the unit number
    main_address = unit_match.group(2)  # Building number
    if unit_match.group(3):  # Street name exists
        main_address += " " + unit_match.group(3)
    
    # Continue with validation using only the main address part
    address = main_address

print(address)  # Output: "12 Example Street"
