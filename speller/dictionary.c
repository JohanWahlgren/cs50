// Implements a dictionary's functionality

#include <ctype.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <math.h>

#include "dictionary.h"

// Represents a node in a hash table
typedef struct node
{
    char word[LENGTH + 1];
    struct node *next;
} node;

// TODO: Choose number of buckets in hash table
const unsigned int N = 18278;

// Hash table
node *table[N];

int word_counter = 0;

// Returns true if word is in dictionary, else false
bool check(const char *word)
{
    int index = hash(word);

    node *head = table[index];

    for(node *cursor = head; cursor != NULL; cursor = cursor->next)
    {
        if(strcasecmp(cursor->word, word) == 0)
        {
            return true;
        }
    }
    return false;
}

// Hashes word to a number
unsigned int hash(const char *word)
{
    unsigned int index = 0;
    int word_length = strlen(word);
    char word_copy[4];
    strncpy(word_copy, word, 3);
    word_copy[3] = '\0';

    if(strlen(word) < 1)
    {
        printf("empty string");
        return 1;
    }

    for(int i = 0; i < 3; i++)
    {
        word_copy[i] = toupper(word_copy[i]);

        if(i == word_length - 1)
        {
            break;
        }
    }

    int considered_chars = fmin(word_length, 3);

    for (int i = 0; i < considered_chars; i++)
    {
        index += (word_copy[i] - 'A' + 1) * pow(26, considered_chars - 1 - i);
    }
    return index;
}

// Loads dictionary into memory, returning true if successful, else false
bool load(const char *dictionary)
{
    FILE *file = fopen(dictionary, "r");
    if(file == NULL)
    {
        printf("An error occured could not read file");
        return false;
    }

    char letters_in_word[LENGTH + 1];

    while(fscanf(file, "%s", letters_in_word) != EOF)
    {
        node *new_node = malloc(sizeof(node));

        if(new_node == NULL)
        {
            printf("Not enough memory");
            word_counter = 0;
            return false;
        }

        word_counter++;

        strcpy(new_node->word, letters_in_word);
        new_node->next = NULL;

        int hash_index = hash(letters_in_word);

        if(table[hash_index] == NULL)
        {
            table[hash_index] = new_node;
        }
        else
        {
            new_node->next = table[hash_index];
            table[hash_index] = new_node;
        }
    }

    fclose(file);
    return true;
}

// Returns number of words in dictionary if loaded, else 0 if not yet loaded
unsigned int size(void)
{
    return word_counter;
}

// Unloads dictionary from memory, returning true if successful, else false
bool unload(void)
{
    node *cursor = NULL;
    node *tmp = NULL;

    for(int i = 0; i < N; i++)
    {
        cursor = table[i];
        while(cursor != NULL)
        {
            tmp = cursor;
            cursor = cursor->next;
            free(tmp);
        }
    }

    return true;
}
