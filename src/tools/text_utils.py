def concatenate_text(input: list):
    result: str = ""
    for i, item in enumerate(input, start=1):
        result += str(item).strip()  # Convert CrewOutput to string
        result += "\n\n"
    return result
