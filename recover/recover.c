#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main(int argc, char *argv[])
{
    // Accept a single command-line argument
    if (argc != 2)
    {
        printf("Usage: ./recover FILE\n");
        return 1;
    }

    FILE *memory_card = fopen(argv[1], "r");
    if(memory_card == NULL)
    {
        printf("Could not open file");
        return 2;
    }

    typedef uint8_t BYTE;

    BYTE buffer[512];

    int jpeg_counter = 0;

    FILE* image = NULL;

    char filename[8] = {0};

    while(fread(buffer, sizeof(BYTE) * 512, 1, memory_card))
    {
        if(buffer[0] == 0xFF && buffer[1] == 0xD8 && buffer[2] == 0xFF && (buffer[3]&0xF0) == 0xE0)
        {
            if(image != NULL)
            {
                fclose(image);
            }

            sprintf(filename, "%03d.jpg", jpeg_counter);
            image = fopen(filename, "w");
            jpeg_counter++;
        }

        if(image != NULL)
        {
            fwrite(buffer, sizeof(BYTE) * 512, 1, image);
        }
    }

    if(image != NULL)
    {
        fclose(image);
    }

    fclose(memory_card);

    return 0;
}
