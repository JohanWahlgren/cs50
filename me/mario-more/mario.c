#include <stdio.h>
#include <cs50.h>

int main(void)
{
    int pyramid_height;
    do
    {
        pyramid_height = get_int("Enter the height of the pyramid ");
    }
    while(pyramid_height < 1 || pyramid_height > 8);

    for(int i = 0; i < pyramid_height; i++)
        {
            for(int j = (pyramid_height-i); j > 1 ; j--)
            {
            printf(" ");
            }
            for(int j = 0; j<=i ; j++)
            {
            printf("#");
            }
            printf("  ");
            for(int j = 0; j<=i ; j++)
            {
            printf("#");
            }
            printf("\n");
        }
}
