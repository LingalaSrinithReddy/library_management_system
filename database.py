import sqlite3
import csv
import json

class Database:
    def __init__(self, db_name="library.db"):
        self.conn = sqlite3.connect(db_name)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT NOT NULL UNIQUE,
                available INTEGER NOT NULL DEFAULT 1
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                member_id INTEGER NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                return_date TEXT,
                FOREIGN KEY (book_id) REFERENCES books(id),
                FOREIGN KEY (member_id) REFERENCES members(id)
            )
        """)

        self.conn.commit()
    
    def close(self):
        self.conn.close()

    # ---------- Books ----------

    def add_book(self, title, author, isbn):
        """Return the new book id (int). Raises ValueError if the ISBN already exists."""
        try:
            cur = self.conn.execute(
                "INSERT INTO books (title, author, isbn) VALUES (?, ?, ?)",
                (title, author, isbn),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            self.conn.rollback()
            raise ValueError("A book with this ISBN already exists")

    def get_book(self, book_id):
        """Return one book as a tuple (id, title, author, isbn, available), or None if not found."""
        cur = self.conn.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        return cur.fetchone()

    def search_books(self, keyword):
        """Return a list of book tuples whose title, author or ISBN contains keyword (empty list if none)."""
        pattern = f"%{keyword}%"
        cur = self.conn.execute(
            "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?",
            (pattern, pattern, pattern),
        )
        return cur.fetchall()

    def list_books(self):
        """Return a list of all book tuples (id, title, author, isbn, available)."""
        cur = self.conn.execute("SELECT * FROM books")
        return cur.fetchall()

    def update_book(self, book_id, title, author, isbn):
        """Update a book's details and return None. Raises ValueError if not found or ISBN is a duplicate."""
        try:
            cur = self.conn.execute(
                "UPDATE books SET title = ?, author = ?, isbn = ? WHERE id = ?",
                (title, author, isbn, book_id),
            )
        except sqlite3.IntegrityError:
            self.conn.rollback()
            raise ValueError("A book with this ISBN already exists")
        if cur.rowcount == 0:
            raise ValueError("Book not found")
        self.conn.commit()

    def update_availability(self, book_id, status):
        """Set available to status (1 = available, 0 = issued) and return None. Raises ValueError if invalid or not found."""
        if status not in (0, 1):
            raise ValueError("Status must be 0 or 1")
        cur = self.conn.execute(
            "UPDATE books SET available = ? WHERE id = ?",
            (status, book_id),
        )
        if cur.rowcount == 0:
            raise ValueError("Book not found")
        self.conn.commit()

    # ---------- Members ----------

    def add_member(self, name, email):
        """Return the new member id (int)."""
        cur = self.conn.execute(
            "INSERT INTO members (name, email) VALUES (?, ?)",
            (name, email),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_member(self, member_id):
        """Return one member as a tuple (id, name, email), or None if not found."""
        cur = self.conn.execute("SELECT * FROM members WHERE id = ?", (member_id,))
        return cur.fetchone()

    def update_member(self, member_id, name, email):
        """Update a member's details and return None. Raises ValueError if not found."""
        cur = self.conn.execute(
            "UPDATE members SET name = ?, email = ? WHERE id = ?",
            (name, email, member_id),
        )
        if cur.rowcount == 0:
            raise ValueError("Member not found")
        self.conn.commit()

    # ---------- Issues ----------
    # DESIGN DECISION: Database updates books.available itself inside
    # issue_book (-> 0) and return_book (-> 1), in the same commit.
    # Library must NOT call update_availability for issuing or returning.

    def issue_book(self, book_id, member_id, issue_date, due_date):
        """Return the new issue id (int). Raises ValueError if book/member not found or book already issued."""
        book = self.get_book(book_id)
        if book is None:
            raise ValueError("Book not found")
        if self.get_member(member_id) is None:
            raise ValueError("Member not found")
        if book[4] != 1:
            raise ValueError("Book already issued")

        try:
            cur = self.conn.execute(
                "INSERT INTO issues (book_id, member_id, issue_date, due_date) VALUES (?, ?, ?, ?)",
                (book_id, member_id, issue_date, due_date),
            )
            self.conn.execute("UPDATE books SET available = 0 WHERE id = ?", (book_id,))
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.Error:
            self.conn.rollback()
            raise

    def return_book(self, book_id, return_date):
        """Record the return date on the active issue, mark the book available, and return None. Raises ValueError if the book was not issued."""
        issue = self.get_active_issue(book_id)
        if issue is None:
            raise ValueError("Book was not issued")

        try:
            self.conn.execute(
                "UPDATE issues SET return_date = ? WHERE id = ?",
                (return_date, issue[0]),
            )
            self.conn.execute("UPDATE books SET available = 1 WHERE id = ?", (book_id,))
            self.conn.commit()
        except sqlite3.Error:
            self.conn.rollback()
            raise

    def get_active_issue(self, book_id):
        """Return the unreturned issue tuple (id, book_id, member_id, issue_date, due_date, return_date), or None."""
        cur = self.conn.execute(
            "SELECT * FROM issues WHERE book_id = ? AND return_date IS NULL",
            (book_id,),
        )
        return cur.fetchone()

    def list_issued_books(self):
        """Return a list of tuples (issue_id, book_title, member_name, issue_date, due_date) for all open issues."""
        cur = self.conn.execute(
            """
            SELECT issues.id, books.title, members.name, issues.issue_date, issues.due_date
            FROM issues
            JOIN books ON issues.book_id = books.id
            JOIN members ON issues.member_id = members.id
            WHERE issues.return_date IS NULL
            """
        )
        return cur.fetchall()
    # ---------- Files ----------

    def export_books_csv(self, filename="books.csv"):
        """Write a header row and all books to a CSV file and return None."""
        books = self.list_books()
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "title", "author", "isbn", "available"])
            writer.writerows(books)

    def backup_to_json(self, filename="backup.json"):
        """Write all books, members and issues to one JSON file and return None."""
        data = {
            "books": self.conn.execute("SELECT * FROM books").fetchall(),
            "members": self.conn.execute("SELECT * FROM members").fetchall(),
            "issues": self.conn.execute("SELECT * FROM issues").fetchall(),
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)