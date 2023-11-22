from colorama import Fore, Style


# Example of using color-coded print statements:
def print_info(message):
    print(f"{Fore.BLUE}{message}{Style.RESET_ALL}")


def print_success(message):
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")


def print_warning(message):
    print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")


def print_error(message):
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")
