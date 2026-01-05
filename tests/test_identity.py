"""Tests for identity management (v0.2)."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from wve.cli import main
from wve.identity import (
    Channel,
    Identity,
    add_channel_to_identity,
    add_video_to_identity,
    create_identity,
    delete_identity,
    extract_video_id,
    get_identity_dir,
    identity_exists,
    list_identities,
    load_identity,
    parse_channel_url,
    save_identity,
    slugify,
)


@pytest.fixture
def temp_identity_dir(tmp_path, monkeypatch):
    """Use temporary directory for identity storage."""
    identity_dir = tmp_path / "identities"
    identity_dir.mkdir()
    monkeypatch.setattr("wve.identity.DEFAULT_IDENTITY_DIR", identity_dir)
    return identity_dir


class TestSlugify:
    def test_simple_name(self):
        assert slugify("John Doe") == "john-doe"

    def test_special_characters(self):
        assert slugify("E.M. Burlingame") == "em-burlingame"

    def test_multiple_spaces(self):
        assert slugify("John   Doe") == "john-doe"

    def test_dashes(self):
        assert slugify("Jean-Claude Van Damme") == "jean-claude-van-damme"


class TestParseChannelUrl:
    def test_youtube_handle(self):
        ch = parse_channel_url("https://youtube.com/@exikiex")
        assert ch.platform == "youtube"
        assert ch.id == "exikiex"
        assert ch.url == "https://youtube.com/@exikiex"

    def test_youtube_channel_id(self):
        ch = parse_channel_url("https://youtube.com/channel/UC123abc")
        assert ch.id == "UC123abc"

    def test_youtube_custom_url(self):
        ch = parse_channel_url("https://youtube.com/c/MyChannel")
        assert ch.id == "MyChannel"

    def test_fallback(self):
        ch = parse_channel_url("https://vimeo.com/user123")
        assert ch.id == "https://vimeo.com/user123"


class TestExtractVideoId:
    def test_watch_url(self):
        assert extract_video_id("https://www.youtube.com/watch?v=abc123def") == "abc123def"

    def test_short_url(self):
        assert extract_video_id("https://youtu.be/abc123def") == "abc123def"

    def test_embed_url(self):
        assert extract_video_id("https://youtube.com/embed/abc123def") == "abc123def"

    def test_raw_id(self):
        assert extract_video_id("abc123def") == "abc123def"

    def test_with_params(self):
        assert extract_video_id("https://www.youtube.com/watch?v=abc123&t=100") == "abc123"


class TestIdentityModel:
    def test_create_minimal(self):
        i = Identity(slug="test", display_name="Test Person")
        assert i.slug == "test"
        assert i.display_name == "Test Person"
        assert i.aliases == []
        assert i.channels == []
        assert i.confirmed_videos == []

    def test_create_full(self):
        i = Identity(
            slug="test",
            display_name="Test Person",
            aliases=["Test", "T. Person"],
            channels=[Channel(platform="youtube", id="UC123", url="https://youtube.com/@test")],
            confirmed_videos=["vid1", "vid2"],
        )
        assert len(i.aliases) == 2
        assert len(i.channels) == 1
        assert len(i.confirmed_videos) == 2


class TestIdentityStorage:
    def test_save_and_load(self, temp_identity_dir):
        identity = Identity(slug="test-person", display_name="Test Person")
        save_identity(identity)

        loaded = load_identity("test-person")
        assert loaded.slug == identity.slug
        assert loaded.display_name == identity.display_name

    def test_identity_exists(self, temp_identity_dir):
        assert not identity_exists("nonexistent")
        create_identity("Test Person", slug="test-person")
        assert identity_exists("test-person")

    def test_list_identities_empty(self, temp_identity_dir):
        assert list_identities() == []

    def test_list_identities(self, temp_identity_dir):
        create_identity("Person One", slug="one")
        create_identity("Person Two", slug="two")
        identities = list_identities()
        assert len(identities) == 2
        slugs = [i.slug for i in identities]
        assert "one" in slugs
        assert "two" in slugs

    def test_delete_identity(self, temp_identity_dir):
        create_identity("Test", slug="test")
        assert identity_exists("test")
        assert delete_identity("test")
        assert not identity_exists("test")

    def test_delete_nonexistent(self, temp_identity_dir):
        assert not delete_identity("nonexistent")


class TestCreateIdentity:
    def test_basic(self, temp_identity_dir):
        i = create_identity("Skinner Layne")
        assert i.slug == "skinner-layne"
        assert i.display_name == "Skinner Layne"

    def test_custom_slug(self, temp_identity_dir):
        i = create_identity("E.M. Burlingame", slug="em")
        assert i.slug == "em"

    def test_with_channel(self, temp_identity_dir):
        i = create_identity("Test", channel_url="https://youtube.com/@testchannel")
        assert len(i.channels) == 1
        assert i.channels[0].id == "testchannel"

    def test_with_aliases(self, temp_identity_dir):
        i = create_identity("Test Person", aliases=["Test", "T.P."])
        assert len(i.aliases) == 2

    def test_duplicate_raises(self, temp_identity_dir):
        create_identity("Test Person")
        with pytest.raises(ValueError, match="already exists"):
            create_identity("Test Person")


class TestAddChannel:
    def test_add_channel(self, temp_identity_dir):
        create_identity("Test", slug="test")
        i = add_channel_to_identity("test", "https://youtube.com/@channel1")
        assert len(i.channels) == 1

        i = add_channel_to_identity("test", "https://youtube.com/@channel2")
        assert len(i.channels) == 2

    def test_duplicate_channel_raises(self, temp_identity_dir):
        create_identity("Test", slug="test")
        add_channel_to_identity("test", "https://youtube.com/@channel1")
        with pytest.raises(ValueError, match="already exists"):
            add_channel_to_identity("test", "https://youtube.com/@channel1")

    def test_not_found(self, temp_identity_dir):
        with pytest.raises(FileNotFoundError):
            add_channel_to_identity("nonexistent", "https://youtube.com/@test")


class TestAddVideo:
    def test_add_confirmed(self, temp_identity_dir):
        create_identity("Test", slug="test")
        i = add_video_to_identity("test", "vid1", confirmed=True)
        assert "vid1" in i.confirmed_videos
        assert "vid1" not in i.rejected_videos

    def test_add_rejected(self, temp_identity_dir):
        create_identity("Test", slug="test")
        i = add_video_to_identity("test", "vid1", confirmed=False)
        assert "vid1" not in i.confirmed_videos
        assert "vid1" in i.rejected_videos

    def test_move_from_rejected_to_confirmed(self, temp_identity_dir):
        create_identity("Test", slug="test")
        add_video_to_identity("test", "vid1", confirmed=False)
        i = add_video_to_identity("test", "vid1", confirmed=True)
        assert "vid1" in i.confirmed_videos
        assert "vid1" not in i.rejected_videos

    def test_idempotent(self, temp_identity_dir):
        create_identity("Test", slug="test")
        add_video_to_identity("test", "vid1", confirmed=True)
        i = add_video_to_identity("test", "vid1", confirmed=True)
        assert i.confirmed_videos.count("vid1") == 1


class TestIdentityCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_create(self, runner, temp_identity_dir):
        result = runner.invoke(main, ["identity", "create", "Test Person"])
        assert result.exit_code == 0
        assert "Created identity: test-person" in result.output

    def test_create_with_options(self, runner, temp_identity_dir):
        result = runner.invoke(
            main,
            [
                "identity", "create", "Skinner Layne",
                "-c", "https://youtube.com/@exikiex",
                "-a", "Skinner",
                "-w", "https://skinnerlayne.com",
            ],
        )
        assert result.exit_code == 0
        i = load_identity("skinner-layne")
        assert len(i.channels) == 1
        assert "Skinner" in i.aliases

    def test_create_json(self, runner, temp_identity_dir):
        result = runner.invoke(main, ["identity", "create", "Test Person", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["slug"] == "test-person"

    def test_list_empty(self, runner, temp_identity_dir):
        result = runner.invoke(main, ["identity", "list"])
        assert result.exit_code == 0
        assert "No identities found" in result.output

    def test_list(self, runner, temp_identity_dir):
        create_identity("Person One", slug="one")
        create_identity("Person Two", slug="two")
        result = runner.invoke(main, ["identity", "list"])
        assert result.exit_code == 0
        assert "one" in result.output
        assert "two" in result.output

    def test_list_json(self, runner, temp_identity_dir):
        create_identity("Test Person")
        result = runner.invoke(main, ["identity", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1

    def test_show(self, runner, temp_identity_dir):
        create_identity("Test Person", slug="test")
        result = runner.invoke(main, ["identity", "show", "test"])
        assert result.exit_code == 0
        assert "Test Person" in result.output

    def test_show_not_found(self, runner, temp_identity_dir):
        result = runner.invoke(main, ["identity", "show", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_add_channel(self, runner, temp_identity_dir):
        create_identity("Test", slug="test")
        result = runner.invoke(main, ["identity", "add-channel", "test", "https://youtube.com/@chan"])
        assert result.exit_code == 0
        assert "Added channel" in result.output

    def test_add_video(self, runner, temp_identity_dir):
        create_identity("Test", slug="test")
        result = runner.invoke(main, ["identity", "add-video", "test", "vid1", "vid2"])
        assert result.exit_code == 0
        assert "2 confirmed" in result.output
        i = load_identity("test")
        assert len(i.confirmed_videos) == 2

    def test_add_video_reject(self, runner, temp_identity_dir):
        create_identity("Test", slug="test")
        result = runner.invoke(main, ["identity", "add-video", "test", "vid1", "--reject"])
        assert result.exit_code == 0
        assert "rejected" in result.output

    def test_delete_with_confirm(self, runner, temp_identity_dir):
        create_identity("Test", slug="test")
        result = runner.invoke(main, ["identity", "delete", "test", "-y"])
        assert result.exit_code == 0
        assert "Deleted" in result.output
        assert not identity_exists("test")

    def test_delete_json(self, runner, temp_identity_dir):
        create_identity("Test", slug="test")
        result = runner.invoke(main, ["identity", "delete", "test", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"]
