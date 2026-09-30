# Практическое занятие №1. Введение, основы работы в командной строке

П.Н. Советов, РТУ МИРЭА

Научиться выполнять простые действия с файлами и каталогами в Linux из командной строки. Сравнить работу в командной строке Windows и Linux.

## Задача 1

Вывести отсортированный в алфавитном порядке список имен пользователей в файле passwd (вам понадобится grep).
```
grep -o '^[^:]*' /etc/passwd | sort
```

<img width="1472" height="1344" alt="image" src="https://github.com/user-attachments/assets/8d97ef35-ca27-4e19-86b6-b57814c05a97" />


## Задача 2

Вывести данные /etc/protocols в отформатированном и отсортированном порядке для 5 наибольших портов, как показано в примере ниже:

```
[root@localhost etc]# cat /etc/protocols ...
142 rohc
141 wesp
140 shim6
139 hip
138 manet
```
```
awk '!/^#/ && NF >= 2 {print $2, $1}' /etc/protocols | sort -k1 -n -r | head -n 5
```
<img width="2354" height="292" alt="image" src="https://github.com/user-attachments/assets/76529bc4-f3a1-44a7-a83c-5696c948a5dc" />


## Задача 3

Написать программу banner средствами bash для вывода текстов, как в следующем примере (размер баннера должен меняться!):

```
[root@localhost ~]# ./banner "Hello from RTU MIREA!"
+-----------------------+
| Hello from RTU MIREA! |
+-----------------------+
```
```
labex:pract1/ $ cat > banner << 'EOF'
text="$1"

if [ -z "$text" ]; then
    echo "Ispolzovanie: $0 \"text\""
    exit 1
fi

line=$(printf '%*s' "$((${#text} + 2))" '' | tr ' ' '-')

echo "+${line}+"
echo "| ${text} |"
echo "+${line}+"
EOF

```
<img width="456" height="158" alt="image" src="https://github.com/user-attachments/assets/f4968a07-5724-48e3-9ac5-aeecefdc4855" />

## Задача 4

Написать программу для вывода всех идентификаторов (по правилам C/C++ или Java) в файле (без повторений).

Пример для hello.c:
```
h hello include int main n printf return stdio void world
```
```
cat > identifiers << 'EOF'
#!/bin/bash
if [ -z "$1" ]; then
    echo "Using: $0 <file>"                                                                                                                                                                
    exit 1
fi
grep -oE '[A-Za-z_][A-Za-z0-9_]*' "$1" | sort -u | tr '\n' ' '
echo
EOF
```
Cоздание файла:
```
$ cat > hi.c << 'EOF'   
#include <stdio.h>
int main() {
    printf("Hihihi hahahaha\n");
    return 0;
}
EOF
```
Запуск:
```
./identifiers hi.c
```
<img width="921" height="76" alt="image" src="https://github.com/user-attachments/assets/3c626600-c2f4-49f1-89ec-4f4376f6905c" />


## Задача 5

Написать программу для регистрации пользовательской команды (правильные права доступа и копирование в /usr/local/bin).

Например, пусть программа называется reg:
```
./reg banner
```
В результате для banner задаются правильные права доступа и сам banner копируется в /usr/local/bin.

```
cat > reg << 'EOF'
#!/bin/bash
if [ -z "$1" ]; then
    echo "Использование: $0 <файл>"
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "Ошибка: файл $1 не найден"
    exit 1
fi

chmod +x "$1"

if [ -w /usr/local/bin ]; then
    cp "$1" /usr/local/bin/
else
    sudo cp "$1" /usr/local/bin/
fi

echo "Команда $1 успешно зарегистрирована в /usr/local/bin/"
EOF

chmod +x reg
```
Запускаем команду
```
./reg banner
which banner
banner "Labex test"
```
<img width="580" height="150" alt="image" src="https://github.com/user-attachments/assets/9c2931d9-d692-4831-a761-b0c0c73b9246" />


## Задача 6

Написать программу для проверки наличия комментария в первой строке файлов с расширением c, js и py.
```
cat > check_comment << 'EOF'
#!/bin/bash
dir="${1:-.}"

if [ ! -d "$dir" ]; then
    echo "Error: $dir is not a directory"
    exit 1
fi

find "$dir" -type f \( -name '*.c' -o -name '*.js' -o -name '*.py' \) | while read -r file; do
    first_line=$(head -n 1 "$file")
    case "$file" in
        *.c|*.js)
            if [[ "$first_line" =~ ^[[:space:]]*// ]]; then
                echo "$file: has comment"
            else
                echo "$file: no comment"
            fi
            ;;
        *.py)
            if [[ "$first_line" =~ ^[[:space:]]*# ]]; then
                echo "$file: has comment"
            else
                echo "$file: no comment"
            fi
            ;;
    esac
done
EOF

chmod +x check_comment
```

Создание тестовых файлов
```
cat > test.c << 'EOF'
// Это комментарий
int main() { return 0; }
EOF

cat > test.py << 'EOF'
# Комментарий
print("hello")
EOF

cat > test.js << 'EOF'
let x = 5;
EOF
```

Запуск:
```
./check_comment .
```
<img width="520" height="154" alt="image" src="https://github.com/user-attachments/assets/f2f96a26-c9b7-446d-9b94-2e4d1a83b300" />

## Задача 7

Написать программу для нахождения файлов-дубликатов (имеющих 1 или более копий содержимого) по заданному пути (и подкаталогам).
Код:
```
cat > find_dups << 'EOF'
#!/bin/bash
dir="${1:-.}"

if [ ! -d "$dir" ]; then
    echo "Ошибка: $dir не является директорией"
    exit 1
fi

find "$dir" -type f -exec md5sum {} + | sort | uniq -w32 -D
EOF

chmod +x find_dups
```

Создание тестовых файлов:
```
mkdir -p testdir/a testdir/b
echo "hello" > testdir/a/f1.txt
echo "hello" > testdir/b/f2.txt
echo "world" > testdir/a/f3.txt
```

Запуск:
```
./find_dups testdir
```

<img width="818" height="108" alt="image" src="https://github.com/user-attachments/assets/a0beab06-ad50-4499-af95-c01f9523a44e" />


## Задача 8

Написать программу, которая находит все файлы в данном каталоге с расширением, указанным в качестве аргумента и архивирует все эти файлы в архив tar.

Код:
```
cat > archive_by_ext << 'EOF'
#!/bin/bash
dir="$1"
ext="$2"

if [ -z "$dir" ] || [ -z "$ext" ]; then
    echo "Использование: $0 <каталог> <расширение>"
    exit 1
fi

if [ ! -d "$dir" ]; then
    echo "Ошибка: $dir не является директорией"
    exit 1
fi

archive="archive_${ext}_$(date +%Y%m%d_%H%M%S).tar.gz"

find "$dir" -type f -name "*.$ext" -print0 | tar -czvf "$archive" --null -T -

echo "Архив создан: $archive"
EOF

chmod +x archive_by_ext
```

Создание тестовых файлов:
```
mkdir -p docs
echo "one" > docs/a.txt
echo "two" > docs/b.txt
echo "three" > docs/c.md
```

Запуск:
```
./archive_by_ext docs txt
ls -la
```

<img width="1277" height="805" alt="image" src="https://github.com/user-attachments/assets/6ed8d4c4-9748-4174-a4c6-1d4daa4bd5c4" />


## Задача 9

Написать программу, которая заменяет в файле последовательности из 4 пробелов на символ табуляции. Входной и выходной файлы задаются аргументами.

Код:
```
cat > spaces_to_tabs << 'EOF'
#!/bin/bash
input="$1"
output="$2"

if [ -z "$input" ] || [ -z "$output" ]; then
    echo "Использование: $0 <входной_файл> <выходной_файл>"
    exit 1
fi

if [ ! -f "$input" ]; then
    echo "Ошибка: файл $input не найден"
    exit 1
fi

sed 's/    /\t/g' "$input" > "$output"
echo "Готово: $output"
EOF

chmod +x spaces_to_tabs
```

Создание файлa:
```
printf '    int main() {\n        return 0;\n    }\n' > input.txt
```

Проверка содержимого:
```
cat -A input.txt
```
```
^I
```
- символ табуляции
<img width="849" height="234" alt="image" src="https://github.com/user-attachments/assets/f31820fd-3d68-4284-b360-e0fab761b6f2" />


## Задача 10

Написать программу, которая выводит названия всех пустых текстовых файлов в указанной директории. Директория передается в программу параметром. 

Код:
```
cat > empty_text_files << 'EOF'
#!/bin/bash
dir="${1:-.}"

if [ ! -d "$dir" ]; then
    echo "Ошибка: $dir не является директорией"
    exit 1
fi

find "$dir" -maxdepth 1 -type f -size 0 | while read -r file; do
    if file "$file" | grep -q "text"; then
        echo "$file"
    fi
done
EOF

chmod +x empty_text_files
```

Создание файлов:
```
mkdir -p testdir2
touch testdir2/empty1.txt
touch testdir2/empty2.txt
echo "text" > testdir2/not_empty.txt
touch testdir2/empty_bin
```

Запуск:
```
./empty_text_files testdir2
```

В моей директории нет пустых файлов, поэтому программа ничего не выводит
