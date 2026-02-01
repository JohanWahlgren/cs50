#include "helpers.h"
#include <math.h>

// Convert image to grayscale
void grayscale(int height, int width, RGBTRIPLE image[height][width])
{
    for(int i = 0; i < height; i++)
    {
        for(int j = 0; j < width; j++)
        {
            int red_value = image[i][j].rgbtRed;
            int green_value = image[i][j].rgbtGreen;
            int blue_value = image[i][j].rgbtBlue;

            float average = (red_value + green_value + blue_value) / 3.0;
            int rounded_average = round(average);

            image[i][j].rgbtRed = rounded_average;
            image[i][j].rgbtGreen = rounded_average;
            image[i][j].rgbtBlue = rounded_average;
        }
    }
    return;
}

// Convert image to sepia
void sepia(int height, int width, RGBTRIPLE image[height][width])
{
    int sepia_red = 0;
    int sepia_green = 0;
    int sepia_blue = 0;

    for(int i = 0; i < height; i++)
    {
        for(int j = 0; j < width; j++)
        {
            float sepia_red_float = 0.393 * image[i][j].rgbtRed + 0.769 * image[i][j].rgbtGreen + 0.189 * image[i][j].rgbtBlue;
            float sepia_green_float = 0.349 * image[i][j].rgbtRed + 0.686 * image[i][j].rgbtGreen + 0.168 * image[i][j].rgbtBlue;
            float sepia_blue_float = 0.272 * image[i][j].rgbtRed + 0.534 * image[i][j].rgbtGreen + 0.131 * image[i][j].rgbtBlue;

            if(sepia_red_float > 255)
            {
                sepia_red = 255;
            }
            else
            {
                sepia_red = (int)round(sepia_red_float);
            }

            if(sepia_green_float > 255)
            {
                sepia_green = 255;
            }
            else
            {
                sepia_green = (int)round(sepia_green_float);
            }

            if(sepia_blue_float > 255)
            {
                sepia_blue = 255;
            }
            else
            {
                sepia_blue = (int)round(sepia_blue_float);
            }

            image[i][j].rgbtRed = sepia_red;
            image[i][j].rgbtGreen = sepia_green;
            image[i][j].rgbtBlue = sepia_blue;
        }
    }
    return;
}

// Reflect image horizontally
void reflect(int height, int width, RGBTRIPLE image[height][width])
{
    for(int i = 0; i < height; i++)
    {
        for(int j = 0; j < width / 2; j++)
        {
            RGBTRIPLE temp = image[i][j];
            image[i][j] = image[i][width - (j + 1)];
            image[i][width - (j +1)] = temp;
        }
    }
    return;
}

// Blur image
void blur(int height, int width, RGBTRIPLE image[height][width])
{
    RGBTRIPLE copy[height][width];
    for(int i = 0; i < height; i++)
    {
        for(int j = 0; j < width; j++)
        {
            copy[i][j] = image[i][j];
        }
    }

    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            int red_total = 0;
            int green_total = 0;
            int blue_total = 0;
            float divider = 0.0;

            for(int k = -1; k < 2; k++)
            {
                for(int l = -1; l < 2; l ++)
                {
                    if(i + k < 0 || i + k >= height)
                    {
                        continue;
                    }

                    if(j + l < 0 || j + l >= width)
                    {
                        continue;
                    }
                    red_total += copy[i + k][j + l].rgbtRed;
                    green_total += copy[i + k][j + l].rgbtGreen;
                    blue_total += copy[i + k][j + l].rgbtBlue;

                    divider++;
                }
            }
            image[i][j].rgbtRed = round(red_total / divider);
            image[i][j].rgbtGreen = round(green_total / divider);
            image[i][j].rgbtBlue = round(blue_total / divider);
        }
    }
    return;
}
