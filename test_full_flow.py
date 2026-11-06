import os
import sqlite3
from database import Database

TEST_DB = "test.db"
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

db = Database(TEST_DB)
passed = failed = 0


def check(name, actual, expected):
    global passed, failed
    if actual == expected:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}\n      expected: {expected!r}\n      got:      {actual!r}")


def expect_clean_error(name, message, func, *args):
    """Pass only if func raises ValueError. A raw sqlite3 error or any other exception fails."""
    global passed, failed
    try:
        func(*args)
    except ValueError as e:
        if message is None or str(e) == message:
            passed += 1
            print(f"PASS: {name}")
        else:
            failed += 1
            print(f"FAIL: {name}\n      expected message: {message!r}\n      got message:      {str(e)!r}")
    except sqlite3.Error as e:
        failed += 1
        print(f"FAIL: {name} leaked a raw sqlite3 error: {type(e).__name__}: {e}")
    except Exception as e:
        failed += 1
        print(f"FAIL: {name} raised {type(e).__name__}: {e}")
    else:
        failed += 1
        print(f"FAIL: {name} raised no error")


# ================= PART 1: HAPPY PATH =================
print("\n--- Full flow ---")

book_id = db.add_book("Python Basics", "Jane Doe", "111")
check("add_book returns id", book_id, 1)
member_id = db.add_member("Asha Rao", "asha@example.com")
check("add_member returns id", member_id, 1)

check("book starts available", db.get_book(1)[4], 1)
check("no active issue yet", db.get_active_issue(1), None)

check("issue_book returns issue id", db.issue_book(1, 1, "2026-11-06", "2026-11-20"), 1)
check("book now issued", db.get_book(1)[4], 0)
check("active issue found", db.get_active_issue(1),
      (1, 1, 1, "2026-11-06", "2026-11-20", None))
check("list_issued_books", db.list_issued_books(),
      [(1, "Python Basics", "Asha Rao", "2026-11-06", "2026-11-20")])

check("return_book returns None", db.return_book(1, "2026-11-15"), None)
check("book available again", db.get_book(1)[4], 1)
check("no active issue after return", db.get_active_issue(1), None)
check("list_issued_books empty", db.list_issued_books(), [])

check("search by title", [b[0] for b in db.search_books("python")], [1])
check("search by author", [b[0] for b in db.search_books("jane")], [1])
check("search by ISBN", [b[0] for b in db.search_books("111")], [1])
check("search no match", db.search_books("zzz"), [])

# ================= PART 2: REQUIRED ERROR CASES =================
print("\n--- Required error cases ---")

db.add_book("Learning SQL", "Alan Beaulieu", "222")          # book 2
db.issue_book(2, 1, "2026-11-06", "2026-11-20")              # book 2 is now issued

expect_clean_error("issue an already issued book", "Book already issued",
                   db.issue_book, 2, 1, "2026-11-07", "2026-11-21")
expect_clean_error("return a book never issued", "Book was not issued",
                   db.return_book, 1, "2026-11-16")
expect_clean_error("issue to a missing member", "Member not found",
                   db.issue_book, 1, 999, "2026-11-06", "2026-11-20")
expect_clean_error("issue a missing book", "Book not found",
                   db.issue_book, 999, 1, "2026-11-06", "2026-11-20")

# ================= PART 3: NO RAW sqlite3 ERRORS =================
print("\n--- Every bad operation must be a clean ValueError ---")

expect_clean_error("duplicate ISBN on add", "A book with this ISBN already exists",
                   db.add_book, "Copy", "Someone", "111")
expect_clean_error("add_book with missing title", "Title, author and ISBN are required",
                   db.add_book, None, "Someone", "999")
expect_clean_error("update_book to duplicate ISBN", "A book with this ISBN already exists",
                   db.update_book, 2, "Learning SQL", "Alan Beaulieu", "111")
expect_clean_error("update_book with missing title", "Title, author and ISBN are required",
                   db.update_book, 2, None, "Alan Beaulieu", "222")
expect_clean_error("update missing book", "Book not found",
                   db.update_book, 999, "X", "Y", "555")
expect_clean_error("update_availability bad status", "Status must be 0 or 1",
                   db.update_availability, 1, 5)
expect_clean_error("update_availability missing book", "Book not found",
                   db.update_availability, 999, 1)
expect_clean_error("add_member with missing name", "Name and email are required",
                   db.add_member, None, "x@example.com")
expect_clean_error("update_member with missing email", "Name and email are required",
                   db.update_member, 1, "Asha", None)
expect_clean_error("update missing member", "Member not found",
                   db.update_member, 999, "X", "x@example.com")
expect_clean_error("issue_book with no dates", "Issue date and due date are required",
                   db.issue_book, 1, 1, None, None)
expect_clean_error("return_book with no date", "Return date is required",
                   db.return_book, 2, None)

# Lookups should never raise, only return None or []
check("get_book missing returns None", db.get_book(999), None)
check("get_member missing returns None", db.get_member(999), None)
check("get_active_issue missing returns None", db.get_active_issue(999), None)

# ================= PART 4: DATA STAYED CONSISTENT =================
print("\n--- Consistency after all the errors ---")

check("book 2 still issued (0)", db.get_book(2)[4], 0)
check("book 2 still has its open issue", db.get_active_issue(2) is not None, True)
check("book 1 still available (1)", db.get_book(1)[4], 1)
check("exactly 2 books", len(db.list_books()), 2)
check("exactly 1 member", db.get_member(2), None)

db.close()
print(f"\n{passed} passed, {failed} failed")