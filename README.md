# Эмулятор языка оболочки ОС

Конфигурационное управление, 3 семестр (осень 2026/2027), группа ИКБО-42-25.
Сборник практических работ № 1, **вариант 1**.

## 1. Общее описание

Эмулятор командной строки UNIX-подобной ОС: консольное приложение (CLI),
которое показывает приглашение к вводу, разбирает введённые строки и
выполняет команды над виртуальной файловой системой (VFS), которая целиком
хранится в памяти. Язык реализации — Python 3.9+, сторонние библиотеки
не нужны.

Ход работы по этапам (каждый этап — отдельный коммит):

| Этап | Содержание                                   | 
|------|----------------------------------------------|
| 1    | REPL: приглашение, парсер, команды-заглушки  | 
| 2    | Конфигурация: параметры запуска и скрипт     | 
| 3    | Виртуальная файловая система (VFS)           | 


Структура проекта:

```
src/shell_emulator/   исходный код эмулятора
tests/                модульные тесты (test_*.py)
tests/scripts/        bash-скрипты, которые запускают эмулятор из реальной ОС
tests/startup/        стартовые скрипты на языке эмулятора (*.emu)
tests/vfs/            каталоги для проверки загрузки VFS
Makefile, run.sh      запуск и тесты
```

## 2. Описание всех функций и настроек

### Параметры командной строки

| Параметр        | Описание                                  | По умолчанию |
|-----------------|-------------------------------------------|--------------|
| `--vfs ПУТЬ`    | Каталог на диске, из которого загружается VFS | VFS по умолчанию |
| `--script ПУТЬ` | Путь к стартовому скрипту                 | не задан     |
| `-h`, `--help`  | Справка                                   |              |

Сразу после запуска эмулятор выводит все параметры (отладочный вывод):

```
[debug] startup parameters:
[debug]   vfs    = tests/vfs/deep
[debug]   script = tests/startup/basic.emu
```

Незаданный параметр выводится как `<not set>`. Неизвестный параметр или
параметр без значения: сообщение об использовании и код возврата 2.

Порядок запуска: параметры, загрузка VFS, стартовый скрипт, интерактивный
диалог.

### Виртуальная файловая система (VFS)

- Источник VFS — каталог на диске (`--vfs ПУТЬ`). Его дерево каталогов и
  файлов целиком читается в память. Дальше все операции идут только в
  памяти, исходные данные на диске не распаковываются и не меняются.
- Файлы хранятся как байты, поэтому поддерживается любое содержимое.
- Если `--vfs` не указан, в памяти создаётся VFS по умолчанию:
  `/etc/motd`, `/home/user`, `/tmp`.
- После загрузки выводится строка `[info]` с источником VFS и числом
  каталогов (без корневого) и файлов.
- Ошибки загрузки: сообщение `error: ...` и код возврата 1, стартовый скрипт
  не запускается.

| Ситуация                                | Сообщение                                      |
|-----------------------------------------|------------------------------------------------|
| путь не существует                      | `VFS not found: ПУТЬ`                          |
| путь — не каталог                       | `invalid VFS format: not a directory: ПУТЬ`    |
| внутри каталога символическая ссылка    | `invalid VFS format: symbolic link is not supported: ПУТЬ` |
| внутри каталога специальный файл        | `invalid VFS format: unsupported file type: ПУТЬ` |
| нельзя прочитать каталог или файл       | `cannot read ПУТЬ: причина`                    |

### Стартовый скрипт

Файл в кодировке UTF-8 (допускаются BOM и переводы строк Windows), в котором
каждая строка — команда эмулятора.

- Команды выполняются последовательно.
- На экране отображается и ввод (приглашение и команда), и вывод, то есть
  выполнение выглядит как диалог с пользователем. Пустые строки не
  показываются, комментарии (`# ...`) показываются и ничего не делают.
- Ошибочные строки (неизвестная команда, ошибка разбора, ошибка команды)
  пропускаются. Об ошибке сообщается в поток ошибок в формате
  `файл: line N: сообщение`, выполнение продолжается.
- Команда `exit` прерывает скрипт и завершает эмулятор с заданным кодом.
- Если скрипт закончился без `exit`, эмулятор переходит в обычный
  интерактивный режим.
- Если скрипт нельзя прочитать (нет файла, это каталог, не UTF-8), выводится
  `error: cannot read startup script ...` и эмулятор завершается с кодом 1.

### Приглашение к вводу

Формируется из данных реальной ОС: `имя_пользователя@имя_хоста:~$`.
Имя пользователя берётся через `getpass.getuser()`, имя хоста — через
`socket.gethostname()`. Если имя пользователя определить нельзя
(например, в контейнере без записи в `passwd`), подставляется `user`.

### Парсер

Строка делится на слова по пробельным символам.

- `$VAR` и `${VAR}` заменяются значениями переменных окружения реальной ОС
  (например, `$HOME`). Неизвестная переменная даёт пустую строку, как в bash:
  слово без кавычек, которое целиком состоит из такой переменной, пропадает
  (`ls $NOPE x` даёт `args=['x']`), а `"$NOPE"` остаётся пустым аргументом.
  Результат подстановки не разбивается на слова.
- Двойные кавычки `"..."` объединяют слова в один аргумент, внутри них
  переменные раскрываются. В одинарных кавычках `'...'` текст сохраняется
  как есть.
- Слово, которое начинается с `#`, открывает комментарий до конца строки.
- Незакрытая кавычка — ошибка разбора, строка не выполняется.

### Команды

| Команда           | Описание                                                  |
|-------------------|-----------------------------------------------------------|
| `ls [...]`        | Заглушка: выводит своё имя и аргументы                    |
| `cd [...]`        | Заглушка: выводит своё имя и аргументы                    |
| `vfs-save ПУТЬ`   | Сохраняет состояние VFS на диск в исходном формате        |
| `exit [N]`        | Завершает эмулятор с кодом `N` (по умолчанию 0, по модулю 256) |

Формат вывода заглушек: `имя: args=[список аргументов]`.

**`vfs-save ПУТЬ`** записывает VFS на диск в исходном формате, то есть как
дерево каталогов и файлов с теми же именами и содержимым (права доступа и
время изменения не сохраняются). Недостающие каталоги пути создаются. Чтобы
не затереть чужие данные, путь должен быть новым или указывать на пустой
каталог. При успехе выводится `VFS saved to ПУТЬ`.

| Ситуация                                      | Сообщение                                      |
|-----------------------------------------------|------------------------------------------------|
| нет аргумента                                 | `vfs-save: missing path operand`               |
| больше одного аргумента                       | `vfs-save: too many arguments`                 |
| путь — существующий файл                      | `vfs-save: cannot save VFS: ПУТЬ already exists and is not a directory` |
| каталог не пуст                               | `vfs-save: cannot save VFS: directory ПУТЬ is not empty` |
| путь совпадает с каталогом-источником или лежит в нём | `vfs-save: cannot save VFS: ПУТЬ is the source directory or inside it` |
| ошибка записи на диск                         | `vfs-save: cannot save VFS to ПУТЬ: причина`   |

### Обработка ошибок

Ошибки выводятся в поток ошибок, эмулятор продолжает работу:

- неизвестная команда: `foo: command not found`;
- незакрытая кавычка: `syntax error: unexpected end of line, ...`;
- `exit abc`: `exit: abc: numeric argument required`, завершение с кодом 2;
- `exit 1 2`: `exit: too many arguments`, эмулятор не завершается;
- ошибки `vfs-save`: см. таблицу выше.

`Ctrl-C` сбрасывает текущую строку, `Ctrl-D` завершает работу так же, как
`exit`.

## 3. Команды для сборки и запуска тестов

Сборка не требуется. Нужен только Python 3.9 или новее (для скриптов
в `tests/scripts` ещё и bash).

```bash
make run          # запуск эмулятора без параметров
make test         # все тесты: модульные и bash-скрипты
make test-unit    # только модульные тесты (unittest)
make test-scripts # только bash-скрипты tests/scripts/stage*.sh
make clean        # удалить служебные файлы Python
```

Запуск с параметрами:

```bash
./run.sh --vfs tests/vfs/deep
./run.sh --script tests/startup/basic.emu
./run.sh --vfs ПУТЬ_К_VFS --script ПУТЬ_К_СКРИПТУ
```

Без `make` и `run.sh`:

```bash
PYTHONPATH=src python3 -m shell_emulator --vfs tests/vfs/deep
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash tests/scripts/stage3_all_commands.sh
```

Bash-скрипты в `tests/scripts` запускают эмулятор с разными параметрами и
вариантами VFS, показывают его диалог на экране и проверяют вывод, коды
возврата и содержимое сохранённых каталогов (`diff -r`). Каждый скрипт
заканчивается строкой `PASS` или `FAILED`.

| Скрипт                    | Что проверяет                                          |
|---------------------------|--------------------------------------------------------|
| `stage2_no_params.sh`     | запуск без параметров                                  |
| `stage2_vfs_param.sh`     | параметр `--vfs` (две формы записи)                    |
| `stage2_script_param.sh`  | параметр `--script`, ввод и вывод скрипта на экране    |
| `stage2_all_params.sh`    | оба параметра сразу, в любом порядке                   |
| `stage2_script_errors.sh` | пропуск ошибочных строк, нет файла, каталог вместо файла |
| `stage2_cli_errors.sh`    | неизвестный параметр, параметр без значения, `--help`  |
| `stage3_vfs_minimal.sh`   | минимальная VFS: один файл и пустой каталог            |
| `stage3_vfs_files.sh`     | VFS с несколькими файлами                              |
| `stage3_vfs_deep.sh`      | VFS с вложенностью больше трёх уровней                 |
| `stage3_vfs_default.sh`   | VFS по умолчанию (без `--vfs`)                         |
| `stage3_vfs_errors.sh`    | нет каталога, файл вместо каталога, ссылка внутри VFS  |
| `stage3_all_commands.sh`  | `tests/startup/all_commands.emu`: все команды, режимы и ошибки |

Каталоги для проверки VFS лежат в `tests/vfs`: `minimal` (один файл),
`several_files` (пять файлов), `deep` (5 каталогов, 6 файлов, до четырёх
уровней вложенности). Стартовые скрипты эмулятора лежат в `tests/startup`.

## 4. Примеры использования

Приглашение зависит от вашей ОС, ниже показан пример для пользователя
`student` на хосте `host`.

Интерактивный режим (`./run.sh`):

```
student@host:~$ ls -l /tmp "my docs"
ls: args=['-l', '/tmp', 'my docs']
student@host:~$ cd $HOME
cd: args=['/home/student']
student@host:~$ cd '$HOME'
cd: args=['$HOME']
student@host:~$ echo $HOME
echo: command not found
student@host:~$ ls "unclosed
syntax error: unexpected end of line, missing closing "
student@host:~$ exit 3
```

Стартовый скрипт без ошибок
(`./run.sh --script tests/startup/basic.emu`):

```
[debug] startup parameters:
[debug]   vfs    = <not set>
[debug]   script = tests/startup/basic.emu
[info] no VFS path given, default in-memory VFS created: 4 directories, 1 files
student@host:~$ # Стартовый скрипт: основные возможности эмулятора
student@host:~$ ls
ls: args=[]
student@host:~$ ls -l /tmp
ls: args=['-l', '/tmp']
student@host:~$ cd $HOME
cd: args=['/home/student']
student@host:~$ cd "$HOME/my docs"
cd: args=['/home/student/my docs']
student@host:~$ cd '$HOME'
cd: args=['$HOME']
student@host:~$ exit
```

Стартовый скрипт с ошибками
(`./run.sh --vfs tests/vfs/deep --script tests/startup/with_errors.emu`):

```
[debug] startup parameters:
[debug]   vfs    = tests/vfs/deep
[debug]   script = tests/startup/with_errors.emu
[info] VFS loaded from tests/vfs/deep: 5 directories, 6 files
student@host:~$ # Стартовый скрипт с ошибками: ошибочные строки пропускаются
student@host:~$ ls first
ls: args=['first']
student@host:~$ unknown_command arg
tests/startup/with_errors.emu: line 3: unknown_command: command not found
student@host:~$ ls "unclosed quote
tests/startup/with_errors.emu: line 4: syntax error: unexpected end of line, missing closing "
student@host:~$ cd second
cd: args=['second']
student@host:~$ exit 1 2
tests/startup/with_errors.emu: line 6: exit: too many arguments
student@host:~$ ls third
ls: args=['third']
student@host:~$ exit 7
```

Эмулятор завершился с кодом 7. Строка `ls never-executed` после `exit 7`
не выполняется.

Загрузка VFS из каталога и её сохранение
(`VFS_OUT=/home/student/vfs-out ./run.sh --vfs tests/vfs/deep --script tests/startup/save_vfs.emu`):

```
[debug] startup parameters:
[debug]   vfs    = tests/vfs/deep
[debug]   script = tests/startup/save_vfs.emu
[info] VFS loaded from tests/vfs/deep: 5 directories, 6 files
student@host:~$ # Сохранение загруженной VFS на диск.
student@host:~$ # Каталог для сохранения задаётся переменной окружения VFS_OUT.
student@host:~$ vfs-save $VFS_OUT
VFS saved to /home/student/vfs-out
student@host:~$ exit
```

Повторное сохранение в тот же каталог (он уже не пуст) даёт ошибку, работа
продолжается:

```
student@host:~$ vfs-save $VFS_OUT
tests/startup/save_vfs.emu: line 3: vfs-save: cannot save VFS: directory /home/student/vfs-out is not empty
student@host:~$ exit
```

VFS по умолчанию (`./run.sh --script tests/startup/save_vfs.emu`):

```
[debug] startup parameters:
[debug]   vfs    = <not set>
[debug]   script = tests/startup/save_vfs.emu
[info] no VFS path given, default in-memory VFS created: 4 directories, 1 files
...
```

Ошибки загрузки VFS (код возврата 1):

```
$ ./run.sh --vfs no_such_dir
[debug] startup parameters:
[debug]   vfs    = no_such_dir
[debug]   script = <not set>
error: VFS not found: no_such_dir

$ ./run.sh --vfs tests/vfs/minimal/hello.txt
[debug] startup parameters:
[debug]   vfs    = tests/vfs/minimal/hello.txt
[debug]   script = <not set>
error: invalid VFS format: not a directory: tests/vfs/minimal/hello.txt
```

Скрипт не найден (`./run.sh --script nope.emu`, код возврата 1):

```
[debug] startup parameters:
[debug]   vfs    = <not set>
[debug]   script = nope.emu
error: cannot read startup script nope.emu: No such file or directory
```

Все команды, режимы и ошибки одним скриптом
(`bash tests/scripts/stage3_all_commands.sh`, фрагмент вывода):

```
student@host:~$ vfs-save $VFS_OUT
VFS saved to /tmp/tmp.XXXXXX/saved
student@host:~$ vfs-save
tests/startup/all_commands.emu: line 31: vfs-save: missing path operand
student@host:~$ vfs-save one two
tests/startup/all_commands.emu: line 32: vfs-save: too many arguments
student@host:~$ vfs-save $VFS_SRC
tests/startup/all_commands.emu: line 35: vfs-save: cannot save VFS: tests/vfs/deep is the source directory or inside it
...
PASS: stage3_all_commands.sh
```
