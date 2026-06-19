import pytest
from rssmds.cli import main
from rssmds import db


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def populated_db(db_path):
    conn = db.connect(db_path)
    db.add_feed(conn, "https://example.com/feed.xml", title="Example")
    db.upsert_entry(conn, 1, "guid-1", "First Post", "https://example.com/1", "summary", "2025-01-01T00:00:00")
    db.upsert_entry(conn, 1, "guid-2", "Second Post", "https://example.com/2", "summary", "2025-01-02T00:00:00")
    conn.commit()
    conn.close()
    return db_path


class TestAddCommand:
    def test_add_feed(self, db_path, capsys):
        main(["--db", db_path, "add", "https://example.com/feed.xml"])
        out = capsys.readouterr().out
        assert "Added feed" in out

    def test_add_duplicate(self, db_path, capsys):
        main(["--db", db_path, "add", "https://example.com/feed.xml"])
        with pytest.raises(SystemExit):
            main(["--db", db_path, "add", "https://example.com/feed.xml"])


class TestRemoveCommand:
    def test_remove_feed(self, populated_db, capsys):
        main(["--db", populated_db, "remove", "1"])
        out = capsys.readouterr().out
        assert "Removed" in out

    def test_remove_nonexistent(self, db_path):
        with pytest.raises(SystemExit):
            main(["--db", db_path, "remove", "999"])


class TestFeedsCommand:
    def test_list_feeds(self, populated_db, capsys):
        main(["--db", populated_db, "feeds"])
        out = capsys.readouterr().out
        assert "Example" in out
        assert "example.com/feed.xml" in out

    def test_no_feeds(self, db_path, capsys):
        main(["--db", db_path, "feeds"])
        out = capsys.readouterr().out
        assert "No feeds" in out


class TestListCommand:
    def test_list_entries(self, populated_db, capsys):
        main(["--db", populated_db, "list"])
        out = capsys.readouterr().out
        assert "First Post" in out or "Second Post" in out

    def test_list_empty(self, db_path, capsys):
        main(["--db", db_path, "list"])
        out = capsys.readouterr().out
        assert "No entries" in out

    def test_list_limit(self, populated_db, capsys):
        main(["--db", populated_db, "list", "--limit", "1"])
        out = capsys.readouterr().out
        lines = [l for l in out.strip().split("\n") if l.strip()]
        assert len(lines) == 1


class TestReadCommand:
    def test_read_entry(self, populated_db, capsys):
        main(["--db", populated_db, "read", "1"])
        out = capsys.readouterr().out
        assert "First Post" in out

    def test_read_nonexistent(self, populated_db):
        with pytest.raises(SystemExit):
            main(["--db", populated_db, "read", "999"])


class TestMarkReadCommand:
    def test_mark_all_read(self, populated_db, capsys):
        main(["--db", populated_db, "mark-read", "--all"])
        out = capsys.readouterr().out
        assert "Marked all" in out

        main(["--db", populated_db, "list", "--unread"])
        out = capsys.readouterr().out
        assert "No entries" in out

    def test_mark_feed_read(self, populated_db, capsys):
        main(["--db", populated_db, "mark-read", "--feed", "1"])
        out = capsys.readouterr().out
        assert "feed 1" in out

    def test_mark_read_no_args(self, populated_db):
        with pytest.raises(SystemExit):
            main(["--db", populated_db, "mark-read"])


class TestStatsCommand:
    def test_stats(self, populated_db, capsys):
        main(["--db", populated_db, "stats"])
        out = capsys.readouterr().out
        assert "Example" in out
        assert "2" in out


class TestExportCommand:
    def test_export_json_stdout(self, populated_db, capsys):
        main(["--db", populated_db, "export", "json"])
        out = capsys.readouterr().out
        import json
        data = json.loads(out)
        assert len(data) == 2

    def test_export_opml_stdout(self, populated_db, capsys):
        main(["--db", populated_db, "export", "opml"])
        out = capsys.readouterr().out
        assert "<opml" in out

    def test_export_json_to_file(self, populated_db, tmp_path, capsys):
        outfile = str(tmp_path / "out.json")
        main(["--db", populated_db, "export", "json", "-o", outfile])
        import json
        with open(outfile) as f:
            data = json.load(f)
        assert len(data) == 2


class TestNoCommand:
    def test_no_command_exits(self, db_path):
        with pytest.raises(SystemExit):
            main(["--db", db_path])
