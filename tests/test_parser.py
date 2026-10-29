"""Тесты разбора строк и раскрытия переменных окружения."""

import unittest

from shell_emulator.errors import ParseError
from shell_emulator.parser import expand_vars, parse_line

ENV = {"HOME": "/home/student", "NAME": "world", "EMPTY": ""}


class ExpandVarsTest(unittest.TestCase):
    """Подстановка значений переменных."""

    def test_plain_variable(self):
        """$VAR заменяется значением переменной."""
        result = expand_vars("$HOME/docs", ENV)
        self.assertEqual(result, "/home/student/docs")

    def test_braces(self):
        """${VAR} позволяет дописать текст сразу после имени."""
        self.assertEqual(expand_vars("${NAME}ly", ENV), "worldly")

    def test_unknown_variable_is_empty(self):
        """Неизвестная переменная раскрывается в пустую строку."""
        self.assertEqual(expand_vars("a$NOPE.b", ENV), "a.b")

    def test_lone_dollar_stays(self):
        """Знак $ без имени переменной остаётся как есть."""
        self.assertEqual(expand_vars("cost: $ 5", ENV), "cost: $ 5")


class ParseLineTest(unittest.TestCase):
    """Разбиение строки на слова."""

    def test_split_by_spaces(self):
        """Слова разделяются любым числом пробелов."""
        result = parse_line("  ls   -l  dir ", ENV)
        self.assertEqual(result, ["ls", "-l", "dir"])

    def test_empty_line(self):
        """Пустая и пробельная строки дают пустой список."""
        self.assertEqual(parse_line("", ENV), [])
        self.assertEqual(parse_line("   \t ", ENV), [])

    def test_variables_in_arguments(self):
        """Переменные раскрываются в любом слове строки."""
        self.assertEqual(parse_line("cd $HOME", ENV), ["cd", "/home/student"])

    def test_double_quotes_group_and_expand(self):
        """В двойных кавычках слова склеиваются, переменные раскрываются."""
        result = parse_line('ls "my $NAME dir"', ENV)
        self.assertEqual(result, ["ls", "my world dir"])

    def test_single_quotes_keep_text(self):
        """В одинарных кавычках переменные не раскрываются."""
        self.assertEqual(parse_line("ls '$HOME'", ENV), ["ls", "$HOME"])

    def test_empty_quotes_make_empty_word(self):
        """Пустые кавычки дают пустой аргумент."""
        self.assertEqual(parse_line('ls ""', ENV), ["ls", ""])

    def test_adjacent_fragments_join(self):
        """Фрагменты без пробелов между ними образуют одно слово."""
        self.assertEqual(parse_line("ls a'b c'$NAME", ENV), ["ls", "ab cworld"])

    def test_expansion_is_not_split(self):
        """Значение переменной с пробелами остаётся одним словом."""
        env = {"DIR": "my dir"}
        self.assertEqual(parse_line("cd $DIR", env), ["cd", "my dir"])

    def test_empty_expansion_disappears(self):
        """Слово из одной пустой переменной пропадает, как в bash."""
        self.assertEqual(parse_line("ls $NOPE x", ENV), ["ls", "x"])
        self.assertEqual(parse_line("ls $EMPTY", ENV), ["ls"])

    def test_quoted_empty_expansion_stays(self):
        """В кавычках пустое значение остаётся пустым аргументом."""
        self.assertEqual(parse_line('ls "$NOPE"', ENV), ["ls", ""])

    def test_empty_expansion_inside_word(self):
        """Пустая переменная внутри слова даёт только остальной текст."""
        self.assertEqual(parse_line("ls a$NOPE", ENV), ["ls", "a"])

    def test_comment(self):
        """Текст после # в начале слова считается комментарием."""
        self.assertEqual(parse_line("ls dir # note", ENV), ["ls", "dir"])
        self.assertEqual(parse_line("# only comment", ENV), [])

    def test_hash_inside_word(self):
        """Знак # внутри слова не начинает комментарий."""
        self.assertEqual(parse_line("ls a#b", ENV), ["ls", "a#b"])

    def test_unclosed_quote(self):
        """Незакрытая кавычка приводит к ParseError."""
        with self.assertRaises(ParseError):
            parse_line("ls 'abc", ENV)
        with self.assertRaises(ParseError):
            parse_line('ls "abc', ENV)


if __name__ == "__main__":
    unittest.main()
