from cs50 import get_string

text = get_string("Text: ")

letters = 0
words = 0
sentences = 0

sentence_set = {".", "!", "?"}
alphabet_set = {"a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
                "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"}

for i in range(len(text)):
    if text[i] in sentence_set:
        sentences += 1

    elif text[i] == " ":
        words += 1

    elif text[i] in alphabet_set:
        letters += 1


words += 1


L = (letters / words) * 100
S = (sentences / words) * 100

index = 0.0588 * L - 0.296 * S - 15.8

grade = round(index)

if grade > 16:
    print("Grade 16+")

elif grade < 1:
    print("Before Grade 1")

else:
    print("Grade: ", grade)



