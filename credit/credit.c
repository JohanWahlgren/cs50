#include <stdio.h>
#include <cs50.h>

int main(void)
{
    long long creditCardNumber = get_long_long("Please enter credit card number: ");
    int digit1 = 0;
    int digit2 = 0;
    int numberOfDigits = 0;
    int sumOdds2x = 0;
    int sumEvens = 0;

    while (creditCardNumber > 0)
    {
        digit2 = digit1;
        digit1 = creditCardNumber % 10;

        if (numberOfDigits % 2 == 0)
        {
            sumEvens += digit1;
        }
        else
        {
            int multiple = 2 * digit1;
            sumOdds2x += (multiple / 10) + (multiple % 10);
        }

        creditCardNumber /= 10;
        numberOfDigits++;
    }

    bool is_valid = (sumEvens + sumOdds2x) % 10 == 0;
    int first_two_digits = (digit1 * 10) + digit2;

    if (digit1 == 4 && numberOfDigits >= 13 && numberOfDigits <= 16 && is_valid)
    {
        printf("VISA\n");
    }
    else if ((first_two_digits == 34 || first_two_digits == 37) && numberOfDigits == 15 && is_valid)
    {
        printf("AMEX\n");
    }
    else if (first_two_digits >= 51 && first_two_digits <= 55 && numberOfDigits == 16 && is_valid)
    {
        printf("MASTERCARD\n");
    }
    else
    {
        printf("INVALID\n");
    }
}
