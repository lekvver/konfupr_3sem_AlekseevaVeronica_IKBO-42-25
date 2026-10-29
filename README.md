# Эмулятор языка оболочки ОС

Конфигурационное управление, 3 семестр (осень 2026/2027), группа ИКБО-42-25.
Сборник практических работ № 1, **вариант 1**.

## 1. Общее описание

Эмулятор командной строки UNIX-подобной ОС: консольное приложение (CLI),
которое показывает приглашение к вводу, разбирает введённые строки и
выполняет команды. Язык реализации — Python 3.9+, сторонние библиотеки
не нужны.

Ход работы по этапам (каждый этап — отдельный коммит):

| Этап | Содержание                                   | Статус |
|------|----------------------------------------------|--------|
| 1    | REPL: приглашение, парсер, команды-заглушки  | готово |
| 2    | Конфигурация: параметры запуска и скрипт     | готово |
| 3    | Виртуальная файловая система (VFS)           | —      |

В репозитории также лежит практика 1 (`практика1`, `практика 1.md`).

Структура проекта:

```
src/shell_emulator/   исходный код эмулятора
tests/                модульные тесты (test_*.py)
tests/scripts/        bash-скрипты, которые запускают эмулятор из реальной ОС
tests/startup/        стартовые скрипты на языке эмулятора (*.emu)
Makefile, run.sh      запуск и тесты
```

## 2. Описание всех функций и настроек

### Параметры командной строки

| Параметр        | Описание                                  | По умолчанию |
|-----------------|-------------------------------------------|--------------|
| `--vfs ПУТЬ`    | Путь к физическому расположению VFS       | не задан     |
| `--script ПУТЬ` | Путь к стартовому скрипту                 | не задан     |
| `-h`, `--help`  | Справка                                   |              |

Сразу после запуска эмулятор выводит все параметры (отладочный вывод):

```
[debug] startup parameters:
[debug]   vfs    = /home/student/vfs
[debug]   script = tests/startup/basic.emu
```

Незаданный параметр выводится как `<not set>`. Неизвестный параметр или
параметр без значения: сообщение об использовании и код возврата 2.

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

| Команда    | Описание                                                        |
|------------|-----------------------------------------------------------------|
| `ls [...]` | Заглушка: выводит своё имя и аргументы                          |
| `cd [...]` | Заглушка: выводит своё имя и аргументы                          |
| `exit [N]` | Завершает эмулятор с кодом `N` (по умолчанию 0, берётся по модулю 256) |

Формат вывода заглушек: `имя: args=[список аргументов]`.

### Обработка ошибок

Ошибки выводятся в поток ошибок, эмулятор продолжает работу:

- неизвестная команда: `foo: command not found`;
- незакрытая кавычка: `syntax error: unexpected end of line, ...`;
- `exit abc`: `exit: abc: numeric argument required`, завершение с кодом 2;
- `exit 1 2`: `exit: too many arguments`, эмулятор не завершается.

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
./run.sh --script tests/startup/basic.emu
./run.sh --vfs ПУТЬ_К_VFS --script ПУТЬ_К_СКРИПТУ
```

Без `make` и `run.sh`:

```bash
PYTHONPATH=src python3 -m shell_emulator --script tests/startup/basic.emu
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash tests/scripts/stage2_script_errors.sh
```

Bash-скрипты в `tests/scripts` запускают эмулятор с разными параметрами,
показывают его диалог на экране и проверяют вывод и коды возврата. Каждый
скрипт заканчивается строкой `PASS` или `FAILED`.

| Скрипт                  | Что проверяет                                          |
|-------------------------|--------------------------------------------------------|
| `stage2_no_params.sh`   | запуск без параметров                                  |
| `stage2_vfs_param.sh`   | параметр `--vfs` (две формы записи)                    |
| `stage2_script_param.sh`| параметр `--script`, ввод и вывод скрипта на экране    |
| `stage2_all_params.sh`  | оба параметра сразу, в любом порядке                   |
| `stage2_script_errors.sh` | пропуск ошибочных строк, нет файла, каталог вместо файла |
| `stage2_cli_errors.sh`  | неизвестный параметр, параметр без значения, `--help`  |

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
(`./run.sh --vfs /home/student/vfs --script tests/startup/with_errors.emu`):

```
[debug] startup parameters:
[debug]   vfs    = /home/student/vfs
[debug]   script = tests/startup/with_errors.emu
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

Скрипт не найден (`./run.sh --script nope.emu`, код возврата 1):

```
[debug] startup parameters:
[debug]   vfs    = <not set>
[debug]   script = nope.emu
error: cannot read startup script nope.emu: No such file or directory
```

Запуск bash-скрипта из реальной ОС (`bash tests/scripts/stage2_cli_errors.sh`):

```
=== неизвестный параметр: сообщение об ошибке, код 2 ===
$ python3 -m shell_emulator --bogus
    usage: shell_emulator [-h] [--vfs PATH] [--script PATH]
    shell_emulator: error: unrecognized arguments: --bogus
    [exit code: 2]
...
PASS: stage2_cli_errors.sh
```
