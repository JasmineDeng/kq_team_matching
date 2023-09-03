def prompt_yes_no() -> bool:
    while True:
        input_value = input("Enter y/n: ")
        if input_value == "y":
            return True
        elif input_value == "n":
            return False
        else:
            print(f"Invalid input: {input_value}")
