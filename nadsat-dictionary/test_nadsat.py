#!/usr/bin/env python3
"""
Unit tests for nadsat.py
"""

import unittest
import sys
import subprocess
from pathlib import Path
from io import StringIO
from unittest.mock import patch
import tempfile
import shutil

# Import the functions from nadsat (uses nadsat.py symlink for testing)
from nadsat import load_dictionary_from_data, get_words_by_letter, find_word, display_word


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
        required_fields = {'nadsat', 'english', 'origin', 'original_nadsat'}
        for word in self.words:
            self.assertEqual(set(word.keys()), required_fields)

    def test_synonym_handling(self):
        """Verify 'guff, guffaw' creates two separate searchable entries"""
        guff_entries = [w for w in self.words if w['nadsat'] == 'guff']
        guffaw_entries = [w for w in self.words if w['nadsat'] == 'guffaw']

        self.assertEqual(len(guff_entries), 1)
        self.assertEqual(len(guffaw_entries), 1)

    def test_synonyms_share_same_definition(self):
        """Both synonyms have identical english/origin"""
        guff = next(w for w in self.words if w['nadsat'] == 'guff')
        guffaw = next(w for w in self.words if w['nadsat'] == 'guffaw')

        self.assertEqual(guff['english'], guffaw['english'])
        self.assertEqual(guff['origin'], guffaw['origin'])
        self.assertEqual(guff['english'], 'laugh')

    def test_synonyms_preserve_original_field(self):
        """Both synonyms show 'guff, guffaw' in original_nadsat"""
        guff = next(w for w in self.words if w['nadsat'] == 'guff')
        guffaw = next(w for w in self.words if w['nadsat'] == 'guffaw')

        self.assertEqual(guff['original_nadsat'], 'guff, guffaw')
        self.assertEqual(guffaw['original_nadsat'], 'guff, guffaw')

    def test_non_synonym_words_unchanged(self):
        """Words without commas work normally"""
        droog = next(w for w in self.words if w['nadsat'] == 'droog')

        self.assertEqual(droog['nadsat'], 'droog')
        self.assertEqual(droog['original_nadsat'], 'droog')
        self.assertEqual(droog['english'], 'friend')

    # Removed test_invalid_csv_path since dictionary data is now embedded

    def test_parenthetical_pronunciation_creates_multiple_entries(self):
        """Verify 'horrorshow (xorosho)' creates entries for all forms"""
        # Should have entries for: full form, main word, and alternate
        full_form = [w for w in self.words if w['nadsat'] == 'horrorshow (xorosho)']
        main_word = [w for w in self.words if w['nadsat'] == 'horrorshow']
        alternate = [w for w in self.words if w['nadsat'] == 'xorosho']

        self.assertEqual(len(full_form), 1)
        self.assertEqual(len(main_word), 1)
        self.assertEqual(len(alternate), 1)

    def test_parenthetical_forms_share_same_definition(self):
        """All forms have identical english/origin"""
        full_form = next(w for w in self.words if w['nadsat'] == 'horrorshow (xorosho)')
        main_word = next(w for w in self.words if w['nadsat'] == 'horrorshow')
        alternate = next(w for w in self.words if w['nadsat'] == 'xorosho')

        self.assertEqual(full_form['english'], main_word['english'])
        self.assertEqual(full_form['english'], alternate['english'])
        self.assertEqual(full_form['origin'], main_word['origin'])
        self.assertEqual(full_form['origin'], alternate['origin'])

    def test_parenthetical_forms_preserve_original(self):
        """All forms show original 'horrorshow (xorosho)' in original_nadsat"""
        full_form = next(w for w in self.words if w['nadsat'] == 'horrorshow (xorosho)')
        main_word = next(w for w in self.words if w['nadsat'] == 'horrorshow')
        alternate = next(w for w in self.words if w['nadsat'] == 'xorosho')

        self.assertEqual(full_form['original_nadsat'], 'horrorshow (xorosho)')
        self.assertEqual(main_word['original_nadsat'], 'horrorshow (xorosho)')
        self.assertEqual(alternate['original_nadsat'], 'horrorshow (xorosho)')


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
        nadsat_words = [w['nadsat'] for w in results]
        self.assertIn('droog', nadsat_words)
        self.assertIn('devotchka', nadsat_words)

    def test_get_words_by_letter_case_insensitive(self):
        """'D' and 'd' return same results"""
        results_lower = get_words_by_letter(self.words, 'd')
        results_upper = get_words_by_letter(self.words, 'D')

        self.assertEqual(len(results_lower), len(results_upper))
        self.assertEqual(
            sorted([w['nadsat'] for w in results_lower]),
            sorted([w['nadsat'] for w in results_upper])
        )

    def test_get_words_by_letter_no_matches(self):
        """Returns empty list for letters with no words"""
        results = get_words_by_letter(self.words, 'q')
        self.assertEqual(len(results), 0)

    def test_get_words_includes_both_synonyms(self):
        """Letter 'g' returns both 'guff' and 'guffaw' entries"""
        results = get_words_by_letter(self.words, 'g')
        nadsat_words = [w['nadsat'] for w in results]

        self.assertIn('guff', nadsat_words)
        self.assertIn('guffaw', nadsat_words)

    def test_all_returned_words_start_with_letter(self):
        """Verify all results actually start with requested letter"""
        for letter in ['d', 'v', 'a', 'g', 'h']:
            results = get_words_by_letter(self.words, letter)
            for word in results:
                self.assertTrue(
                    word['nadsat'].lower().startswith(letter.lower()),
                    f"Word '{word['nadsat']}' doesn't start with '{letter}'"
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
        self.assertEqual(result['nadsat'], 'droog')
        self.assertEqual(result['english'], 'friend')

    def test_find_word_case_insensitive(self):
        """'DROOG', 'Droog', 'droog' all work"""
        result_lower = find_word(self.words, 'droog')
        result_upper = find_word(self.words, 'DROOG')
        result_mixed = find_word(self.words, 'Droog')

        self.assertIsNotNone(result_lower)
        self.assertIsNotNone(result_upper)
        self.assertIsNotNone(result_mixed)

        self.assertEqual(result_lower['nadsat'], result_upper['nadsat'])
        self.assertEqual(result_lower['nadsat'], result_mixed['nadsat'])

    def test_find_nonexistent_word(self):
        """Returns None for invalid word"""
        result = find_word(self.words, 'notaword')
        self.assertIsNone(result)

    def test_find_synonym_guff(self):
        """Can find 'guff'"""
        result = find_word(self.words, 'guff')

        self.assertIsNotNone(result)
        self.assertEqual(result['nadsat'], 'guff')
        self.assertEqual(result['english'], 'laugh')

    def test_find_synonym_guffaw(self):
        """Can find 'guffaw'"""
        result = find_word(self.words, 'guffaw')

        self.assertIsNotNone(result)
        self.assertEqual(result['nadsat'], 'guffaw')
        self.assertEqual(result['english'], 'laugh')

    def test_synonyms_return_identical_data(self):
        """Both synonyms return same english/origin"""
        guff = find_word(self.words, 'guff')
        guffaw = find_word(self.words, 'guffaw')

        self.assertEqual(guff['english'], guffaw['english'])
        self.assertEqual(guff['origin'], guffaw['origin'])
        self.assertEqual(guff['original_nadsat'], guffaw['original_nadsat'])

    def test_find_word_with_spaces(self):
        """Handle multi-word entries like 'appy polly loggies'"""
        result = find_word(self.words, 'appy polly loggies')

        self.assertIsNotNone(result)
        self.assertEqual(result['english'], 'apologies')

    def test_find_parenthetical_full_form(self):
        """Can find 'horrorshow (xorosho)' by full form"""
        result = find_word(self.words, 'horrorshow (xorosho)')

        self.assertIsNotNone(result)
        self.assertEqual(result['english'], 'good, well, wonderful, excellent')

    def test_find_parenthetical_main_word(self):
        """Can find 'horrorshow (xorosho)' by main word 'horrorshow'"""
        result = find_word(self.words, 'horrorshow')

        self.assertIsNotNone(result)
        self.assertEqual(result['english'], 'good, well, wonderful, excellent')

    def test_find_parenthetical_alternate(self):
        """Can find 'horrorshow (xorosho)' by alternate 'xorosho'"""
        result = find_word(self.words, 'xorosho')

        self.assertIsNotNone(result)
        self.assertEqual(result['english'], 'good, well, wonderful, excellent')

    def test_parenthetical_all_forms_identical(self):
        """All parenthetical forms return identical data"""
        full = find_word(self.words, 'horrorshow (xorosho)')
        main = find_word(self.words, 'horrorshow')
        alt = find_word(self.words, 'xorosho')

        self.assertEqual(full['english'], main['english'])
        self.assertEqual(full['english'], alt['english'])
        self.assertEqual(full['original_nadsat'], main['original_nadsat'])
        self.assertEqual(full['original_nadsat'], alt['original_nadsat'])


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


class TestMainIntegration(unittest.TestCase):
    """End-to-end tests using subprocess to run the actual script"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.script_path = Path(__file__).parent / 'nadsat'
        cls.original_csv = Path(__file__).parent / 'dictionary.csv'

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
        self.assertIn('Origin:', result.stdout)

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
        self.assertEqual(result['english'], 'good, well, wonderful, excellent')


if __name__ == '__main__':
    unittest.main()
