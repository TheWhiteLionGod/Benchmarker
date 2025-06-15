# Input formatter - converts comma-separated values to parameter format

def format_input(input_string, array_name="arr", array_range="range(1, 100000000)"):
    """
    Takes comma-separated input and formats it into parameter tuples
    
    Args:
        input_string: String with comma-separated values (e.g., "5, 10, 15, -1, 20")
        array_name: Name for the array variable (default: "arr")
        array_range: Range definition for the array (default: "range(1, 100000000)")
    
    Returns:
        Formatted string with array and params definitions
    """
    # Parse the input string
    values = [x.strip() for x in input_string.split(',')]
    
    # Convert to integers (handle potential conversion errors)
    try:
        int_values = [int(x) for x in values]
    except ValueError as e:
        return f"Error: Could not convert all values to integers. {e}"
    
    # Generate the formatted output
    result = f"{array_name} = list({array_range})\n"
    result += "params = [\n"
    
    for value in int_values:
        result += f"    ({array_name}, {value}),\n"
    
    result += "]"
    
    return result

# Example usage
if __name__ == "__main__":
    # Get input from user
    user_input = input("Enter comma-separated values: ")
    
    # Format and display result
    formatted_output = format_input(user_input)
    print("\nFormatted output:")
    print(formatted_output)
    
    # Copy-paste ready version
    print("\n" + "="*50)
    print("COPY-PASTE READY:")
    print("="*50)
    print(formatted_output)