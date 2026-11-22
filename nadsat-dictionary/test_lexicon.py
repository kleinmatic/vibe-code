#!/usr/bin/env python3
"""
Unit tests for lexicon (and its nadsat/newspeak launchers).
"""

import unittest
import sys
import subprocess
from pathlib import Path
from io import StringIO
from unittest.mock import patch
import tempfile
import shutil

import importlib.machinery
import importlib.util

# Load the extensionless `lexicon` script as a module.
_LEXICON_PATH = str(Path(__file__).parent / 'lexicon')
_loader = importlib.machinery.SourceFileLoader('lexicon', _LEXICON_PATH)
_spec = importlib.util.spec_from_loader('lexicon', _loader)
lexicon = importlib.util.module_from_spec(_spec)
_loader.exec_module(lexicon)

display_word = lexicon.display_word
find_word = lexicon.find_word
get_words_by_length = lexicon.get_words_by_length
get_words_by_letter = lexicon.get_words_by_letter
load_dictionary_from_data = lexicon.load_dictionary_from_data


class TestLoadDictionary(unittest.TestCase):
    """Tests for the load_dictionary_from_data() function"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        # Note: tests now use the embedded DICTIONARY_DATA, not test CSV
        cls.words = load_dictionary_from_data()

    def test_load_dictionary_returns_list(self):
        """Verify load_dictionary returns a list"""
        self.assertIsInstance(self.words, list)
        self.assertGreater(len(self.words), 0)

    def test_loaded_words_have_required_fields(self):
        """Check each word has required fields"""
        required_fields = {'term', 'meaning', 'origin', 'type', 'first_appearance', 'original_term'}
        for word in self.words:
            self.assertEqual(set(word.keys()), required_fields)

    def test_synonym_handling(self):
        """Verify 'guff, guffaw' creates two separate searchable entries"""
        guff_entries = [w for w in self.words if w['term'] == 'guff']
        guffaw_entries = [w for w in self.words if w['term'] == 'guffaw']

        self.assertEqual(len(guff_entries), 1)
        self.assertEqual(len(guffaw_entries), 1)

    def test_synonyms_share_same_definition(self):
        """Both synonyms have identical english/origin"""
        guff = next(w for w in self.words if w['term'] == 'guff')
        guffaw = next(w for w in self.words if w['term'] == 'guffaw')

        self.assertEqual(guff['meaning'], guffaw['meaning'])
        self.assertEqual(guff['origin'], guffaw['origin'])
        self.assertEqual(guff['meaning'], 'laugh')

    def test_synonyms_preserve_original_field(self):
        """Both synonyms show 'guff, guffaw' in original_nadsat"""
        guff = next(w for w in self.words if w['term'] == 'guff')
        guffaw = next(w for w in self.words if w['term'] == 'guffaw')

        self.assertEqual(guff['original_term'], 'guff, guffaw')
        self.assertEqual(guffaw['original_term'], 'guff, guffaw')

    def test_non_synonym_words_unchanged(self):
        """Words without commas work normally"""
        droog = next(w for w in self.words if w['term'] == 'droog')

        self.assertEqual(droog['term'], 'droog')
        self.assertEqual(droog['original_term'], 'droog')
        self.assertEqual(droog['meaning'], 'friend')

    # Removed test_invalid_csv_path since dictionary data is now embedded

    def test_parenthetical_pronunciation_creates_multiple_entries(self):
        """Verify 'horrorshow (xorosho)' creates entries for all forms"""
        # Should have entries for: full form, main word, and alternate
        full_form = [w for w in self.words if w['term'] == 'horrorshow (xorosho)']
        main_word = [w for w in self.words if w['term'] == 'horrorshow']
        alternate = [w for w in self.words if w['term'] == 'xorosho']

        self.assertEqual(len(full_form), 1)
        self.assertEqual(len(main_word), 1)
        self.assertEqual(len(alternate), 1)

    def test_parenthetical_forms_share_same_definition(self):
        """All forms have identical english/origin"""
        full_form = next(w for w in self.words if w['term'] == 'horrorshow (xorosho)')
        main_word = next(w for w in self.words if w['term'] == 'horrorshow')
        alternate = next(w for w in self.words if w['term'] == 'xorosho')

        self.assertEqual(full_form['meaning'], main_word['meaning'])
        self.assertEqual(full_form['meaning'], alternate['meaning'])
        self.assertEqual(full_form['origin'], main_word['origin'])
        self.assertEqual(full_form['origin'], alternate['origin'])

    def test_parenthetical_forms_preserve_original(self):
        """All forms show original 'horrorshow (xorosho)' in original_nadsat"""
        full_form = next(w for w in self.words if w['term'] == 'horrorshow (xorosho)')
        main_word = next(w for w in self.words if w['term'] == 'horrorshow')
        alternate = next(w for w in self.words if w['term'] == 'xorosho')

        self.assertEqual(full_form['original_term'], 'horrorshow (xorosho)')
        self.assertEqual(main_word['original_term'], 'horrorshow (xorosho)')
        self.assertEqual(alternate['original_term'], 'horrorshow (xorosho)')


class TestGetWordsByLetter(unittest.TestCase):
    """Tests for the get_words_by_letter() function"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.words = load_dictionary_from_data()

    def test_get_words_by_letter_d(self):
        """Returns words starting with 'd'"""
        results = get_words_by_letter(self.words, 'd')

        self.assertGreater(len(results), 0)
        # Should include droog and devotchka, dva
        terms = [w['term'] for w in results]
        self.assertIn('droog', terms)
        self.assertIn('devotchka', terms)

    def test_get_words_by_letter_case_insensitive(self):
        """'D' and 'd' return same results"""
        results_lower = get_words_by_letter(self.words, 'd')
        results_upper = get_words_by_letter(self.words, 'D')

        self.assertEqual(len(results_lower), len(results_upper))
        self.assertEqual(
            sorted([w['term'] for w in results_lower]),
            sorted([w['term'] for w in results_upper])
        )

    def test_get_words_by_letter_no_matches(self):
        """Returns empty list for letters with no words"""
        results = get_words_by_letter(self.words, 'q')
        self.assertEqual(len(results), 0)

    def test_get_words_includes_both_synonyms(self):
        """Letter 'g' returns both 'guff' and 'guffaw' entries"""
        results = get_words_by_letter(self.words, 'g')
        terms = [w['term'] for w in results]

        self.assertIn('guff', terms)
        self.assertIn('guffaw', terms)

    def test_all_returned_words_start_with_letter(self):
        """Verify all results actually start with requested letter"""
        for letter in ['d', 'v', 'a', 'g', 'h']:
            results = get_words_by_letter(self.words, letter)
            for word in results:
                self.assertTrue(
                    word['term'].lower().startswith(letter.lower()),
                    f"Word '{word['term']}' doesn't start with '{letter}'"
                )


class TestFindWord(unittest.TestCase):
    """Tests for the find_word() function"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.words = load_dictionary_from_data()

    def test_find_existing_word(self):
        """Find 'droog' returns correct entry"""
        result = find_word(self.words, 'droog')

        self.assertIsNotNone(result)
        self.assertEqual(result['term'], 'droog')
        self.assertEqual(result['meaning'], 'friend')

    def test_find_word_case_insensitive(self):
        """'DROOG', 'Droog', 'droog' all work"""
        result_lower = find_word(self.words, 'droog')
        result_upper = find_word(self.words, 'DROOG')
        result_mixed = find_word(self.words, 'Droog')

        self.assertIsNotNone(result_lower)
        self.assertIsNotNone(result_upper)
        self.assertIsNotNone(result_mixed)

        self.assertEqual(result_lower['term'], result_upper['term'])
        self.assertEqual(result_lower['term'], result_mixed['term'])

    def test_find_nonexistent_word(self):
        """Returns None for invalid word"""
        result = find_word(self.words, 'notaword')
        self.assertIsNone(result)

    def test_find_synonym_guff(self):
        """Can find 'guff'"""
        result = find_word(self.words, 'guff')

        self.assertIsNotNone(result)
        self.assertEqual(result['term'], 'guff')
        self.assertEqual(result['meaning'], 'laugh')

    def test_find_synonym_guffaw(self):
        """Can find 'guffaw'"""
        result = find_word(self.words, 'guffaw')

        self.assertIsNotNone(result)
        self.assertEqual(result['term'], 'guffaw')
        self.assertEqual(result['meaning'], 'laugh')

    def test_synonyms_return_identical_data(self):
        """Both synonyms return same english/origin"""
        guff = find_word(self.words, 'guff')
        guffaw = find_word(self.words, 'guffaw')

        self.assertEqual(guff['meaning'], guffaw['meaning'])
        self.assertEqual(guff['origin'], guffaw['origin'])
        self.assertEqual(guff['original_term'], guffaw['original_term'])

    def test_find_word_with_spaces(self):
        """Handle multi-word entries like 'appy polly loggies'"""
        result = find_word(self.words, 'appy polly loggies')

        self.assertIsNotNone(result)
        self.assertEqual(result['meaning'], 'apologies')

    def test_find_parenthetical_full_form(self):
        """Can find 'horrorshow (xorosho)' by full form"""
        result = find_word(self.words, 'horrorshow (xorosho)')

        self.assertIsNotNone(result)
        self.assertEqual(result['meaning'], 'good, well, wonderful, excellent')

    def test_find_parenthetical_main_word(self):
        """Can find 'horrorshow (xorosho)' by main word 'horrorshow'"""
        result = find_word(self.words, 'horrorshow')

        self.assertIsNotNone(result)
        self.assertEqual(result['meaning'], 'good, well, wonderful, excellent')

    def test_find_parenthetical_alternate(self):
        """Can find 'horrorshow (xorosho)' by alternate 'xorosho'"""
        result = find_word(self.words, 'xorosho')

        self.assertIsNotNone(result)
        self.assertEqual(result['meaning'], 'good, well, wonderful, excellent')

    def test_parenthetical_all_forms_identical(self):
        """All parenthetical forms return identical data"""
        full = find_word(self.words, 'horrorshow (xorosho)')
        main = find_word(self.words, 'horrorshow')
        alt = find_word(self.words, 'xorosho')

        self.assertEqual(full['meaning'], main['meaning'])
        self.assertEqual(full['meaning'], alt['meaning'])
        self.assertEqual(full['original_term'], main['original_term'])
        self.assertEqual(full['original_term'], alt['original_term'])


class TestGetWordsByLength(unittest.TestCase):
    """Tests for the get_words_by_length() function."""

    @classmethod
    def setUpClass(cls):
        cls.words = load_dictionary_from_data()

    def test_get_words_by_length(self):
        """Returns words with exactly the requested number of characters."""
        results = get_words_by_length(self.words, 5)

        self.assertGreater(len(results), 0)
        self.assertIn('droog', [word['term'] for word in results])
        self.assertTrue(all(len(word['term']) == 5 for word in results))

    def test_get_words_by_length_no_matches(self):
        """Returns an empty list when no spelling has the requested length."""
        self.assertEqual(get_words_by_length(self.words, 1000), [])


class TestDisplayWord(unittest.TestCase):
    """Tests for the display_word() function"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.words = load_dictionary_from_data()

    def test_display_word_output_format(self):
        """Use captured stdout to verify format"""
        word = find_word(self.words, 'droog')

        with patch('sys.stdout', new=StringIO()) as fake_out:
            display_word(word)
            output = fake_out.getvalue()

        self.assertIn('droog', output)
        self.assertIn('friend', output)
        self.assertIn('English:', output)
        self.assertIn('Origin:', output)

    def test_display_shows_original_nadsat(self):
        """Synonyms show 'guff, guffaw' not individual word"""
        guff = find_word(self.words, 'guff')

        with patch('sys.stdout', new=StringIO()) as fake_out:
            display_word(guff)
            output = fake_out.getvalue()

        self.assertIn('guff, guffaw', output)

    def test_display_includes_all_fields(self):
        """Output contains nadsat, english, and origin"""
        word = find_word(self.words, 'viddy')

        with patch('sys.stdout', new=StringIO()) as fake_out:
            display_word(word)
            output = fake_out.getvalue()

        self.assertIn('viddy', output)
        self.assertIn('see', output)
        self.assertIn('Origin:', output)

    def test_display_can_show_searchable_form(self):
        """Filters can display an individual synonym instead of its source label."""
        word = find_word(self.words, 'guff')

        with patch('sys.stdout', new=StringIO()) as fake_out:
            display_word(word, use_searchable_form=True)
            output = fake_out.getvalue()

        self.assertIn('\nguff\n', output)
        self.assertNotIn('guff, guffaw', output)


class TestMainIntegration(unittest.TestCase):
    """End-to-end tests using subprocess to run the actual script"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.script_path = Path(__file__).parent / 'nadsat'

    def run_script(self, *args):
        """Helper to run the script and capture output"""
        cmd = ['python3', str(self.script_path)] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        return result

    def test_no_arguments_returns_random_word(self):
        """Verify output format, contains valid word"""
        result = self.run_script()

        self.assertEqual(result.returncode, 0)
        self.assertIn('Random Nadsat Word', result.stdout)
        self.assertIn('English:', result.stdout)

    def test_single_letter_returns_words(self):
        """Check returns up to 3 words"""
        result = self.run_script('d')

        self.assertEqual(result.returncode, 0)
        self.assertIn("Starting with 'D'", result.stdout)
        self.assertIn('English:', result.stdout)
        self.assertIn('Origin:', result.stdout)

    def test_single_letter_case_insensitive(self):
        """'D' and 'd' both work"""
        result_lower = self.run_script('d')
        result_upper = self.run_script('D')

        self.assertEqual(result_lower.returncode, 0)
        self.assertEqual(result_upper.returncode, 0)

        # Both should mention the letter (uppercase in output)
        self.assertIn("Starting with 'D'", result_lower.stdout)
        self.assertIn("Starting with 'D'", result_upper.stdout)

    def test_letter_with_no_words(self):
        """Appropriate message for invalid letter"""
        result = self.run_script('q')

        self.assertEqual(result.returncode, 0)
        self.assertIn('No Nadsat words found', result.stdout)

    def test_word_lookup_found(self):
        """'droog' returns definition"""
        result = self.run_script('droog')

        self.assertEqual(result.returncode, 0)
        self.assertIn('droog', result.stdout)
        self.assertIn('friend', result.stdout)

    def test_word_lookup_synonym_guff(self):
        """'guff' works"""
        result = self.run_script('guff')

        self.assertEqual(result.returncode, 0)
        self.assertIn('guff, guffaw', result.stdout)
        self.assertIn('laugh', result.stdout)

    def test_word_lookup_synonym_guffaw(self):
        """'guffaw' works"""
        result = self.run_script('guffaw')

        self.assertEqual(result.returncode, 0)
        self.assertIn('guff, guffaw', result.stdout)
        self.assertIn('laugh', result.stdout)

    def test_word_lookup_parenthetical_main(self):
        """'horrorshow' works (from 'horrorshow (xorosho)')"""
        result = self.run_script('horrorshow')

        self.assertEqual(result.returncode, 0)
        self.assertIn('horrorshow (xorosho)', result.stdout)
        self.assertIn('good, well, wonderful, excellent', result.stdout)

    def test_word_lookup_parenthetical_alternate(self):
        """'xorosho' works (from 'horrorshow (xorosho)')"""
        result = self.run_script('xorosho')

        self.assertEqual(result.returncode, 0)
        self.assertIn('horrorshow (xorosho)', result.stdout)
        self.assertIn('good, well, wonderful, excellent', result.stdout)

    def test_word_lookup_not_found(self):
        """Appropriate message for invalid word"""
        result = self.run_script('notaword')

        self.assertEqual(result.returncode, 0)
        self.assertIn('not found', result.stdout)

    def test_word_lookup_case_insensitive(self):
        """'DROOG' works"""
        result = self.run_script('DROOG')

        self.assertEqual(result.returncode, 0)
        self.assertIn('droog', result.stdout.lower())
        self.assertIn('friend', result.stdout)

    def test_length_short_option_returns_words(self):
        """'-l 5' returns up to three five-character words."""
        result = self.run_script('-l', '5')

        self.assertEqual(result.returncode, 0)
        self.assertIn('of Length 5', result.stdout)
        self.assertIn('English:', result.stdout)

    def test_length_long_option_returns_words(self):
        """'--length 5' supports the descriptive option name."""
        result = self.run_script('--length', '5')

        self.assertEqual(result.returncode, 0)
        self.assertIn('of Length 5', result.stdout)

    def test_length_equals_syntax_returns_words(self):
        """'--length=5' supports conventional equals syntax."""
        result = self.run_script('--length=5')

        self.assertEqual(result.returncode, 0)
        self.assertIn('of Length 5', result.stdout)

    def test_invalid_length_is_rejected(self):
        """Length must be a positive integer."""
        for value in ['nope', '0', '-2']:
            with self.subTest(value=value):
                result = self.run_script('--length', value)
                self.assertEqual(result.returncode, 1)
                self.assertIn('positive integer', result.stderr)

    def test_missing_length_is_rejected(self):
        """The length option requires a value."""
        result = self.run_script('--length')

        self.assertEqual(result.returncode, 1)
        self.assertIn('requires a positive integer', result.stderr)

    def test_length_with_no_matches(self):
        """A valid length with no matches produces a clear message."""
        result = self.run_script('--length', '1000')

        self.assertEqual(result.returncode, 0)
        self.assertIn('No Nadsat words found with length 1000', result.stdout)

    def test_too_many_arguments(self):
        """Shows usage message"""
        result = self.run_script('arg1', 'arg2')

        self.assertEqual(result.returncode, 1)
        self.assertIn('Usage:', result.stdout)


class TestEdgeCases(unittest.TestCase):
    """Special cases and boundary conditions"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.words = load_dictionary_from_data()
        cls.script_path = Path(__file__).parent / 'nadsat'

    def run_script(self, *args):
        """Helper to run the script and capture output"""
        cmd = ['python3', str(self.script_path)] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        return result

    def test_whitespace_handling(self):
        """Trim spaces from input"""
        # The script uses .strip() on argv input
        result = self.run_script('  droog  ')
        self.assertEqual(result.returncode, 0)
        # Should find the word despite spaces
        # (though shell typically strips trailing spaces anyway)

    def test_unicode_handling(self):
        """Russian characters in origin display correctly"""
        word = find_word(self.words, 'droog')

        with patch('sys.stdout', new=StringIO()) as fake_out:
            display_word(word)
            output = fake_out.getvalue()

        # Should contain Cyrillic characters
        self.assertIn('друг', output)

    def test_randomness_variation(self):
        """Multiple runs return different random words (statistical test)"""
        # Run the script 10 times and collect random words
        results = []
        for _ in range(10):
            result = self.run_script()
            results.append(result.stdout)

        # At least some variation should occur (not all identical)
        unique_results = len(set(results))
        self.assertGreater(unique_results, 1,
                          "Random word selection should show variation")

    def test_words_with_parentheses_in_nadsat_field(self):
        """Handle words like 'horrorshow (xorosho)'"""
        result = find_word(self.words, 'horrorshow (xorosho)')

        self.assertIsNotNone(result)
        self.assertEqual(result['meaning'], 'good, well, wonderful, excellent')


class TestNewspeakDictionary(unittest.TestCase):
    """Tests for the Newspeak dictionary data and lookups."""

    @classmethod
    def setUpClass(cls):
        cls.words = load_dictionary_from_data('newspeak')

    def test_dictionaries_are_separate(self):
        nadsat = load_dictionary_from_data('nadsat')
        self.assertIsNone(find_word(nadsat, 'doublethink'))
        self.assertIsNone(find_word(self.words, 'droog'))

    def test_find_newspeak_word(self):
        result = find_word(self.words, 'doubleplusungood')
        self.assertIsNotNone(result)
        self.assertEqual(result['meaning'], 'extremely bad')
        self.assertEqual(result['type'], 'Newspeak')

    def test_capitalized_term_is_case_insensitive(self):
        for query in ['Minitrue', 'minitrue', 'MINITRUE']:
            with self.subTest(query=query):
                result = find_word(self.words, query)
                self.assertIsNotNone(result)
                self.assertEqual(result['original_term'], 'Minitrue')

    def test_only_allowed_terms_have_spaces(self):
        """Terms are for naming servers, so they are single words, except these."""
        allowed = {'Big Brother', 'Airstrip One'}
        spaced = {w['term'] for w in self.words if ' ' in w['term']}
        self.assertEqual(spaced, allowed)

    def test_abbreviations_carry_full_names(self):
        self.assertIn('Ministry of Truth', find_word(self.words, 'minitrue')['meaning'])
        self.assertIn('Thought Police', find_word(self.words, 'thinkpol')['meaning'])
        self.assertIn('Communist International', find_word(self.words, 'comintern')['meaning'])

    def test_requested_terms_present(self):
        for term in ['sexcrime', 'thoughtcrime', 'comintern', 'big brother', 'airstrip one']:
            with self.subTest(term=term):
                self.assertIsNotNone(find_word(self.words, term))

    def test_comma_forms_share_entry(self):
        one = find_word(self.words, 'unperson')
        many = find_word(self.words, 'unpersons')
        self.assertEqual(one['original_term'], 'unperson, unpersons')
        self.assertEqual(one['meaning'], many['meaning'])

    def test_every_entry_has_type_and_first_appearance(self):
        for word in self.words:
            with self.subTest(term=word['term']):
                self.assertTrue(word['meaning'])
                self.assertTrue(word['type'])
                self.assertRegex(word['first_appearance'],
                                 r'^(Part [123], Ch \d+|Appendix)$')

    def test_display_uses_newspeak_labels(self):
        word = find_word(self.words, 'doublethink')
        with patch('sys.stdout', new=StringIO()) as fake_out:
            display_word(word, dictionary='newspeak')
            output = fake_out.getvalue()
        self.assertIn('Meaning:', output)
        self.assertIn('Notes:', output)
        self.assertIn('First appears: Part 1, Ch 1', output)
        self.assertNotIn('English:', output)


class TestDictionarySelection(unittest.TestCase):
    """Tests for choosing a dictionary by option or by launcher name."""

    def run_cmd(self, script, *args):
        cmd = ['python3', str(Path(__file__).parent / script)] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_lexicon_defaults_to_nadsat(self):
        result = self.run_cmd('lexicon', 'droog')
        self.assertEqual(result.returncode, 0)
        self.assertIn('friend', result.stdout)

    def test_dict_option_selects_newspeak(self):
        for args in (['-d', 'newspeak'], ['--dict', 'newspeak'], ['--dict=newspeak']):
            with self.subTest(args=args):
                result = self.run_cmd('lexicon', *args, 'doublethink')
                self.assertEqual(result.returncode, 0)
                self.assertIn('Newspeak Word Definition', result.stdout)

    def test_dict_option_after_other_args(self):
        result = self.run_cmd('lexicon', '-l', '6', '--dict', 'newspeak')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Random Newspeak Word(s) of Length 6', result.stdout)

    def test_newspeak_launcher(self):
        result = self.run_cmd('newspeak', 'Minipax')
        self.assertEqual(result.returncode, 0)
        self.assertIn('the Ministry of Peace', result.stdout)
        self.assertIn('Notes:', result.stdout)

    def test_newspeak_launcher_letter_and_usage(self):
        result = self.run_cmd('newspeak', 'd')
        self.assertIn("Random Newspeak Word(s) Starting with 'D'", result.stdout)
        result = self.run_cmd('newspeak', 'a', 'b')
        self.assertEqual(result.returncode, 1)
        self.assertIn('newspeak <word>', result.stdout)

    def test_help(self):
        result = self.run_cmd('newspeak', '--help')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Usage:', result.stdout)

    def test_version_shows_dictionary_credits(self):
        result = self.run_cmd('newspeak', '--version')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Nineteen Eighty-Four', result.stdout)

    def test_unknown_dictionary_is_rejected(self):
        result = self.run_cmd('lexicon', '--dict', 'klingon', 'x')
        self.assertEqual(result.returncode, 1)
        self.assertIn('unknown dictionary', result.stderr)

    def test_missing_dictionary_name_is_rejected(self):
        result = self.run_cmd('lexicon', '--dict')
        self.assertEqual(result.returncode, 1)
        self.assertIn('requires a dictionary name', result.stderr)


class TestBuildIsCurrent(unittest.TestCase):
    """The embedded data must match data/*.csv (run build.py after editing)."""

    def test_embedded_data_matches_csv(self):
        import csv
        for name in lexicon.DICTIONARY_DATA:
            with self.subTest(dictionary=name):
                path = Path(__file__).parent / 'data' / f'{name}.csv'
                with open(path, newline='', encoding='utf-8') as f:
                    rows = [{k: v for k, v in r.items() if v != '' or k == 'Origin'}
                            for r in csv.DictReader(f)]
                self.assertEqual(lexicon.DICTIONARY_DATA[name], rows,
                                 'Embedded data is stale: run python3 build.py')


if __name__ == '__main__':
    unittest.main()
