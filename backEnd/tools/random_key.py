import string
import random


def get_random_key(length=10):
    """Generate random strs"""
    num_count = random.randint(1, length - 1)
    letter_count = length - num_count
    num_list = [random.choice(string.digits) for _ in range(num_count)]
    letter_list = [random.choice(string.ascii_uppercase) for _ in range(letter_count)]
    all_list = num_list + letter_list
    random.shuffle(all_list)
    return "".join([i for i in all_list])

