from cs50 import get_string
import sys


card_number = get_string("Please enter card number: ")
length = len(card_number)


cursor = length - 1
sum = 0

while cursor >= 1:
    tmp = 2 * int(card_number[cursor - 1])

    if tmp > 9:
        sum += 1 + (tmp % 10)
    else:
        sum += tmp

    cursor -= 2
    tmp = 0


cursor = length - 1

while cursor >= 0:
    sum += int(card_number[cursor])
    cursor -= 2


if sum % 10 != 0:
    print("INVALID")
    sys.exit(1)


n = int(card_number[0:2])

if n == 34 or n == 37 and length == 15:
    print("AMEX")

elif n > 50 and n < 56 and length == 16:
    print("MASTERCARD")

elif n > 39 and n < 50 and (length == 13 or length == 16):
    print("VISA")

else:
    print("INVALID")
