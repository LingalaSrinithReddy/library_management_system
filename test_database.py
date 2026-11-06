import os
from database import Database

TEST_DB = "test.db"

# Start from a clean slate. (If this fails on Windows, close test.db in DB Browser first.)
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

db = Database(TEST_DB)
passed = 0
failed = 0


def check(name, actual, expected):
    """Compare actual with expected and print PASS or FAIL."""
    global passed, failed
    if actual == expected:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}\n      expected: {expected!r}\n      got:      {actual!r}")


def expect_value_error(name, func, *args):
    """Call func(*args) and expect a ValueError. Returns the message for checking."""
    global passed, failed
    try:
        func(*args)
    except ValueError as e:
        passed += 1
        print(f"PASS: {name} (message: {e})")
    except Exception as e:
        failed += 1
        print(f"FAIL: {name} raised {type(e).__name__} instead of ValueError: {e}")
    else:
        failed += 1
        print(f"FAIL: {name} raised no error")


# ---------------- BOOKS ----------------
print("\n--- Books ---")

check("add_book returns id 1", db.add_book("Python Basics", "Jane Doe", "111"), 1)
check("add_book returns id 2", db.add_book("Learning SQL", "Alan Beaulieu", "222"), 2)
check("add_book returns id 3", db.add_book("Data Science", "Jane Smith", "333"), 3)

expect_value_error("duplicate ISBN", db.add_book, "Copy Book", "Someone", "111")
check("duplicate ISBN left 3 books", len(db.list_books()), 3)

check("get_book existing", db.get_book(1), (1, "Python Basics", "Jane Doe", "111", 1))
check("get_book missing id returns None", db.get_book(999), None)

check("list_books count", len(db.list_books()), 3)

# Search by title, author and ISBN
check("search by title", db.search_books("python"),
      [(1, "Python Basics", "Jane Doe", "111", 1)])
check("search by author", db.search_books("Beaulieu"),
      [(2, "Learning SQL", "Alan Beaulieu", "222", 1)])
check("search by ISBN", db.search_books("333"),
      [(3, "Data Science", "Jane Smith", "333", 1)])
check("search matches several", [b[0] for b in db.search_books("Jane")], [1, 3])
check("search no match returns []", db.search_books("zzz"), [])

# update_book
db.update_book(1, "Python Basics 2nd Ed", "Jane Doe", "111")
check("update_book changed the title", db.get_book(1),
      (1, "Python Basics 2nd Ed", "Jane Doe", "111", 1))
expect_value_error("update missing book", db.update_book, 999, "X", "Y", "444")
expect_value_error("update to a duplicate ISBN", db.update_book, 2, "Learning SQL", "Alan Beaulieu", "111")
check("failed update left book 2 unchanged", db.get_book(2),
      (2, "Learning SQL", "Alan Beaulieu", "222", 1))

# update_availability
db.update_availability(1, 0)
check("update_availability sets 0", db.get_book(1)[4], 0)
db.update_availability(1, 1)
check("update_availability sets 1", db.get_book(1)[4], 1)
expect_value_error("availability status 5", db.update_availability, 1, 5)
expect_value_error("availability on missing book", db.update_availability, 999, 1)
db.update_availability(1, 0)   # leave book 1 as issued so you can see it in the viewer

# ---------------- MEMBERS ----------------
print("\n--- Members ---")

check("add_member returns id 1", db.add_member("Asha Rao", "asha@example.com"), 1)
check("get_member existing", db.get_member(1), (1, "Asha Rao", "asha@example.com"))
check("get_member missing id returns None", db.get_member(999), None)

db.update_member(1, "Asha R.", "asha.r@example.com")
check("update_member changed the row", db.get_member(1), (1, "Asha R.", "asha.r@example.com"))
expect_value_error("update missing member", db.update_member, 999, "X", "x@example.com")

# ---------------- SUMMARY ----------------
db.close()
print(f"\n{passed} passed, {failed} failed")