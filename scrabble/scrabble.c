#include <stdio.h>
#include <cs50.h>
#include <string.h>
#include <ctype.h>

int calculatePoints(string s, int points[], char normalCharacters[], char capitalCharacters[]);

int main(void)
{
    string wordPlayer1 = get_string("Player 1: ");
    string wordPlayer2 = get_string("Player 2: ");

    int points[] = {1, 3, 3, 2, 1, 4, 2, 4, 1, 8, 5, 1, 3, 1, 1, 3, 10, 1, 1, 1, 1, 4, 4, 8, 4, 10};
    char normalCharacters[] = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'};
    char capitalCharacters[] = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V' , 'W', 'X' ,'Y', 'Z'};

    int totalPointsP1 = calculatePoints(wordPlayer1, points, normalCharacters, capitalCharacters);
    int totalPointsP2 = calculatePoints(wordPlayer2, points, normalCharacters, capitalCharacters);

    if(totalPointsP1 > totalPointsP2)
    {
        printf("Player 1 wins!\n");
    }
    else if(totalPointsP2 > totalPointsP1)
    {
        printf("Player 2 wins!\n");
    }
    else
    {
        printf("Tie!\n");
    }
}

int calculatePoints(string s, int points[], char normalCharacters[], char capitalCharacters[])
{
    int n = 0;

    for(int i = 0; i < 26; i++)
    {
        for (int j = 0; j < strlen(s); j++)
        if(normalCharacters[i] == s[j])
        {
            n += points[i];
            break;
        }
        else if(capitalCharacters[i] == s[j])
        {
            n += points[i];
            break;
        }
    }
    return n;
}
