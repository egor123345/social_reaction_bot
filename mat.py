
def read_words_from_file(file_path):
    words = []
    with open(file_path, 'r') as words_file:
        for line in words_file.readlines():
            words.append(line.strip())
    return words


def leven_distance(a, b): 
    # "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        a, b = b, a
        n, m = m, n

    current_row = range(n + 1) 
    for i in range(1, m + 1):
        previous_row, current_row = current_row, [i] + [0] * n
        for j in range(1, n + 1):
            add, delete, change = previous_row[j] + 1, current_row[j - 1] + 1, previous_row[j - 1]
            if a[j - 1] != b[i - 1]:
                change += 1
            current_row[j] = min(add, delete, change)

    return current_row[n]

def is_ban_words(words, phrase):
    d =   {'а' : ['а', 'a', '@'],
    'б' : ['б', '6', 'b'],
    'в' : ['в', 'b', 'v'],
    'г' : ['г', 'r', 'g'],
    'д' : ['д', 'd'],
    'е' : ['е', 'e'],
    'ё' : ['ё', 'e'],
    'ж' : ['ж', 'zh', '*'],
    'з' : ['з', '3', 'z'],
    'и' : ['и', 'u', 'i'],
    'й' : ['й', 'u', 'i'],
    'к' : ['к', 'k', 'i{', '|{'],
    'л' : ['л', 'l', 'ji'],
    'м' : ['м', 'm'],
    'н' : ['н', 'h', 'n'],
    'о' : ['о', 'o', '0'],
    'п' : ['п', 'n', 'p'],
    'р' : ['р', 'r', 'p'],
    'с' : ['с', 'c', 's'],
    'т' : ['т', 'm', 't'],
    'у' : ['у', 'y', 'u'],
    'ф' : ['ф', 'f'],
    'х' : ['х', 'x', 'h' , '}{'],
    'ц' : ['ц', 'c', 'u,'],
    'ч' : ['ч', 'ch'],
    'ш' : ['ш', 'sh'],
    'щ' : ['щ', 'sch'],
    'ь' : ['ь', 'b'],
    'ы' : ['ы', 'bi'],
    'ъ' : ['ъ'],
    'э' : ['э', 'e'],
    'ю' : ['ю', 'io'],
    'я' : ['я', 'ya']
    }

    for key, value in d.items():
        for letter in value:
            for phr in phrase:
                if letter == phr:
                    phrase = phrase.replace(phr, key)

    for word in words:
        for part in range(len(phrase)):
            fragment = phrase[part: part+len(word)]
            if leven_distance(fragment, word) <= len(word)*0.18:
                # print(fragment) печатает плохие словечки
                return True
    return False

def calc_ban_words(words, phrases):
    if (len(phrases) == 0):
        return 0
    ban_word_cnt = 0
    for phrase in phrases:
        ban_word_cnt+= int(is_ban_words(words, phrase))
    ban_word_perc = round(ban_word_cnt / len(phrases) * 100, 2)
    return ban_word_perc, ban_word_cnt

# words = read_words_from_file("mat.txt")

# #Фраза, которую будем проверять.
# phrase = input("Введите фразу для проверки: ").lower().replace(" ", "")

# print(is_ban_words(words, phrase))