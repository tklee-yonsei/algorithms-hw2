import unittest

from src.hash_table import HashTable, horner_hash, horner_hash_steps


class HornerHashTests(unittest.TestCase):
    def test_single_character_is_its_code_point_modulo_capacity(self):
        self.assertEqual(horner_hash("a", 8), 97 % 8)

    def test_multiple_characters_use_base_31(self):
        self.assertEqual(horner_hash("ab", 1000), (97 * 31 + 98) % 1000)
        self.assertEqual(horner_hash("abc", 1000), ((97 * 31 + 98) * 31 + 99) % 1000)

    def test_result_is_always_inside_the_table(self):
        for key in ("", "0", "zzzzzzzzzzzzzzzz", "ZZZZZZZZZZZZZZZZ"):
            with self.subTest(key=key):
                self.assertTrue(0 <= horner_hash(key, 8) < 8)

    def test_hash_steps_show_each_horner_calculation(self):
        self.assertEqual(
            list(horner_hash_steps("ab", 8)),
            [(0, "a", 97, 1), (1, "b", 98, 1)],
        )


class HashTableBasicTests(unittest.TestCase):
    def test_new_table_is_empty_with_initial_capacity_8(self):
        table = HashTable()
        self.assertEqual(len(table), 0)
        self.assertEqual(table.capacity, 8)
        self.assertEqual(list(table.items()), [])

    def test_get_returns_stored_value(self):
        table = HashTable()
        table.put("0", "https://example.com")
        self.assertEqual(table.get("0"), "https://example.com")
        self.assertEqual(len(table), 1)

    def test_missing_key_raises_key_error(self):
        table = HashTable()
        with self.assertRaises(KeyError):
            table.get("0")
        table.put("0", "x")
        with self.assertRaises(KeyError):
            table.get("1")

    def test_updating_existing_key_replaces_value_without_growing(self):
        table = HashTable()
        table.put("k", "old")
        table.put("k", "new")
        self.assertEqual(table.get("k"), "new")
        self.assertEqual(len(table), 1)
        self.assertEqual(list(table.items()), [("k", "new")])

    def test_updating_does_not_trigger_expansion(self):
        table = HashTable()
        for key in "abcde":
            table.put(key, key)
        for _ in range(20):
            table.put("a", "again")
        self.assertEqual(len(table), 5)
        self.assertEqual(table.capacity, 8)

    def test_non_string_keys_are_rejected(self):
        table = HashTable()
        for key in (1, None, b"a", ("a",)):
            with self.subTest(key=key):
                with self.assertRaises(TypeError):
                    table.put(key, "value")


class HashTableCollisionTests(unittest.TestCase):
    def test_colliding_keys_are_stored_in_the_same_chain(self):
        keys = ["a", "i", "q"]
        self.assertEqual({horner_hash(key, 8) for key in keys}, {1})
        table = HashTable()
        for key in keys:
            table.put(key, key.upper())

        chain = list(table.slots())[1][1]
        self.assertEqual({key for key, _ in chain}, set(keys))
        for key in keys:
            with self.subTest(key=key):
                self.assertEqual(table.get(key), key.upper())

    def test_chain_lookup_checks_only_nodes_in_the_bucket(self):
        table = HashTable()
        table.put("a", 1)
        table.put("i", 2)
        table.put("q", 3)
        self.assertEqual(table.comparison_count("q"), 1)
        self.assertEqual(table.comparison_count("i"), 2)
        self.assertEqual(table.comparison_count("a"), 3)
        self.assertEqual(table.comparison_count("y"), 3)

    def test_updating_a_chained_key_changes_only_that_key(self):
        table = HashTable()
        table.put("a", "1")
        table.put("i", "2")
        table.put("i", "3")
        self.assertEqual(table.get("a"), "1")
        self.assertEqual(table.get("i"), "3")
        self.assertEqual(len(table), 2)

    def test_missing_key_in_a_nonempty_chain_is_not_found(self):
        table = HashTable()
        table.put("a", "1")
        table.put("i", "2")
        with self.assertRaises(KeyError):
            table.get("q")


class HashTableResizeTests(unittest.TestCase):
    def test_stays_at_capacity_8_up_to_load_factor_0_7(self):
        table = HashTable()
        for key in "abcde":  # 5 / 8 = 0.625
            table.put(key, key)
        self.assertEqual(table.capacity, 8)

    def test_doubles_when_load_factor_exceeds_0_7(self):
        table = HashTable()
        for key in "abcdef":  # 6 / 8 = 0.75
            table.put(key, key)
        self.assertEqual(table.capacity, 16)

    def test_keeps_doubling_as_it_grows(self):
        table = HashTable()
        for index in range(11):  # 11 / 16 = 0.6875
            table.put(str(index), index)
        self.assertEqual(table.capacity, 16)
        table.put("11", 11)  # 12 / 16 = 0.75
        self.assertEqual(table.capacity, 32)

    def test_existing_entries_survive_expansion(self):
        table = HashTable()
        keys = [str(index) for index in range(50)]
        for index, key in enumerate(keys):
            table.put(key, index)
        self.assertEqual(len(table), 50)
        for index, key in enumerate(keys):
            with self.subTest(key=key):
                self.assertEqual(table.get(key), index)

    def test_colliding_entries_remain_in_chains_after_expansion(self):
        table = HashTable()
        keys = ("a", "i", "q", "g", "o")
        for key in keys:
            table.put(key, key)
        table.put("z", "z")  # sixth entry forces expansion
        self.assertEqual(table.capacity, 16)
        for key in (*keys, "z"):
            with self.subTest(key=key):
                self.assertEqual(table.get(key), key)


class HashTableIterationTests(unittest.TestCase):
    def test_items_yields_every_entry_exactly_once(self):
        table = HashTable()
        expected = {}
        for index in range(30):
            key, value = str(index), f"https://example.com/{index}"
            table.put(key, value)
            expected[key] = value
        items = list(table.items())
        self.assertEqual(len(items), 30)
        self.assertEqual(sorted(items), sorted(expected.items()))


class HashTableFixedSizeTests(unittest.TestCase):
    def test_collision_chain_can_grow_without_resizing_the_bucket_array(self):
        table = HashTable(capacity=3, max_load=None)
        for key in ("a", "d", "g", "j"):
            table.put(key, key)
        self.assertEqual(table.capacity, 3)
        self.assertEqual(len(table), 4)
        for key in ("a", "d", "g", "j"):
            with self.subTest(key=key):
                self.assertEqual(table.get(key), key)


if __name__ == "__main__":
    unittest.main()
