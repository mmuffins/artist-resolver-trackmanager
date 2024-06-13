import os
import sys
import pytest
import httpx
import respx
from unittest.mock import AsyncMock, MagicMock, call
from artist_resolver.trackmanager import TrackManager, MbArtistDetails, TrackDetails
from mutagen import id3
from mutagen.id3 import TIT2, TPE1, TALB, TPE2, TIT1, TOAL, TOPE, TPE3, TXXX


def create_mock_trackdetails():
    """
    Returns a track details object with dummy values
    """
    track = TrackDetails("/fake/path/file1.mp3", TrackManager())
    track.title = ["test title"]
    track.artist = ["test artist1"]
    track.album = ["test album"]
    track.album_artist = ["test album_artist"]
    track.grouping = ["test grouping"]
    track.original_album = ["test original_album"]
    track.original_artist = ["test original_artist"]
    track.original_title = ["test original_title"]
    track.product = ["test product"]
    track.artist_relations = ["test artist_relations"]

    return track


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_create_track_file_without_artist_json(respx_mock, mock_id3_tags):
    # Arrange
    manager = TrackManager()
    reference_track = create_mock_trackdetails()
    reference_track.product = "_"
    reference_track.artist = ["test artist1", "(Character 1)"]

    # mock individual id3 calls
    mock_id3_instance = mock_id3_tags(
        {
            "TIT2": reference_track.title,
            "TPE1": reference_track.artist,
            "TALB": reference_track.album,
            "TPE2": reference_track.album_artist,
            "TIT1": reference_track.grouping,
            "TOAL": reference_track.original_album,
            "TOPE": reference_track.original_artist,
            "TPE3": reference_track.original_title,
        }
    )

    # id3.getall("TXXX") returns an empty array to trigger creating simple artist
    mock_id3_instance.getall.return_value = []

    # mock franchise api needed by properly create simple artist objects
    respx_mock.route(
        method="GET",
        port__in=[manager.api_port],
        host=manager.api_host,
        path="/api/franchise",
    ).mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": 1, "name": "_", "aliases": []},
                {"id": 2, "name": "TestFranchise1", "aliases": []},
                {"id": 3, "name": "TestFranchise2", "aliases": []},
                {"id": 4, "name": "TestFranchise3", "aliases": []},
            ],
        )
    )

    # Act
    manager = TrackManager()
    track = TrackDetails("/fake/path/file1.mp3", manager)
    await track.read_file_metadata()

    # Assert
    assert track.title == reference_track.title[0]
    assert track.artist == reference_track.artist
    assert track.album == reference_track.album[0]
    assert track.album_artist == reference_track.album_artist[0]
    assert track.grouping == reference_track.grouping[0]
    assert track.original_album == reference_track.original_album[0]
    assert track.original_artist == reference_track.original_artist
    assert track.original_title == reference_track.original_title[0]
    assert track.product == reference_track.product[0]


@pytest.mark.asyncio
async def test_save_file_metadata_no_changes(mock_id3_tags):
    # Arrange
    track = TrackDetails("/fake/path/file1.mp3", TrackManager())
    track.title = "Same Title"
    track.artist = ["Same Artist"]
    track.album = "Same Album"
    track.album_artist = "Same Album Artist"
    track.grouping = "Same Grouping"
    track.original_album = "Same Original Album"
    track.original_artist = ["Same Original Artist"]
    track.original_title = "Same Original Title"
    track.artist_relations = "Same Artist Relations"
    track.id3 = id3.ID3(track.file_path)

    mock_id3_instance = mock_id3_tags(
        {
            "TIT2": TIT2(encoding=3, text="Same Title"),
            "TPE1": TPE1(encoding=3, text=["Same Artist"]),
            "TALB": TALB(encoding=3, text="Same Album"),
            "TPE2": TPE2(encoding=3, text="Same Album Artist"),
            "TIT1": TIT1(encoding=3, text="Same Grouping"),
            "TOAL": TOAL(encoding=3, text="Same Original Album"),
            "TOPE": TOPE(encoding=3, text=["Same Original Artist"]),
            "TPE3": TPE3(encoding=3, text="Same Original Title"),
        },
        txxx_frames=[
            TXXX(
                encoding=3,
                HashKey="TXXX:artist_relations_json",
                desc="artist_relations_json",
                text="Same Artist Relations",
            )
        ],
    )

    # Act
    track.save_file_metadata()

    # Assert
    mock_id3_instance.__setitem__.assert_not_called()
    mock_id3_instance.delall.assert_not_called()
    mock_id3_instance.save.assert_not_called()


@pytest.mark.asyncio
async def test_save_file_metadata_changes(mock_id3_tags):
    # Arrange
    track = TrackDetails("/fake/path/file1.mp3", TrackManager())
    track.title = "New Title"
    track.artist = ["New Artist"]
    track.album = "New Album"
    track.album_artist = "New Album Artist"
    track.grouping = "New Grouping"
    track.original_album = "New Original Album"
    track.original_artist = ["New Original Artist"]
    track.original_title = "New Original Title"
    track.id3 = id3.ID3(track.file_path)

    mock_id3_instance = mock_id3_tags(
        {
            "TIT2": TIT2(encoding=3, text="Old Title"),
            "TPE1": TPE1(encoding=3, text=["Old Artist"]),
            "TALB": TALB(encoding=3, text="Old Album"),
            "TPE2": TPE2(encoding=3, text="Old Album Artist"),
            "TIT1": TIT1(encoding=3, text="Old Grouping"),
            "TOAL": TOAL(encoding=3, text="Old Original Album"),
            "TOPE": TOPE(encoding=3, text=["Old Original Artist"]),
            "TPE3": TPE3(encoding=3, text="Old Original Title"),
        }
    )

    # Act
    track.save_file_metadata()

    # Assert
    expected_setitem_calls = [
        call("TIT2", TIT2(encoding=3, text=track.title)),
        call("TPE1", TPE1(encoding=3, text="New Artist")),
        call("TALB", TALB(encoding=3, text=track.album)),
        call("TPE2", TPE2(encoding=3, text=track.album_artist)),
        call("TIT1", TIT1(encoding=3, text=track.grouping)),
        call("TOAL", TOAL(encoding=3, text=track.original_album)),
        call("TOPE", TOPE(encoding=3, text=track.original_artist)),
        call("TPE3", TPE3(encoding=3, text=track.original_title)),
    ]

    mock_id3_instance.__setitem__.assert_has_calls(
        expected_setitem_calls, any_order=True
    )
    mock_id3_instance.save.assert_called_once()


@pytest.mark.asyncio
async def test_save_file_metadata_clear_tags(mock_id3_tags):
    # Arrange
    track = TrackDetails("/fake/path/file1.mp3", TrackManager())
    track.title = None
    track.artist = None
    track.album = None
    track.album_artist = None
    track.grouping = None
    track.original_album = None
    track.original_artist = None
    track.original_title = None
    track.id3 = id3.ID3(track.file_path)

    mock_id3_instance = mock_id3_tags(
        {
            "TIT2": TIT2(encoding=3, text="Old Title"),
            "TPE1": TPE1(encoding=3, text=["Old Artist"]),
            "TALB": TALB(encoding=3, text="Old Album"),
            "TPE2": TPE2(encoding=3, text="Old Album Artist"),
            "TIT1": TIT1(encoding=3, text="Old Grouping"),
            "TOAL": TOAL(encoding=3, text="Old Original Album"),
            "TOPE": TOPE(encoding=3, text=["Old Original Artist"]),
            "TPE3": TPE3(encoding=3, text="Old Original Title"),
        }
    )

    # Act
    track.save_file_metadata()

    # Assert
    expected_pop_calls = [
        call("TIT2", None),
        call("TPE1", None),
        call("TALB", None),
        call("TPE2", None),
        call("TIT1", None),
        call("TOAL", None),
        call("TOPE", None),
        call("TPE3", None),
    ]

    mock_id3_instance.pop.assert_has_calls(expected_pop_calls, any_order=True)
    mock_id3_instance.save.assert_not_called()


@pytest.mark.asyncio
async def test_save_file_metadata_partial_changes(mock_id3_tags):
    # Arrange
    track = TrackDetails("/fake/path/file1.mp3", TrackManager())
    track.title = "New Title"
    track.artist = ["New Artist"]
    track.album = "New Album"
    track.album_artist = "Old Album Artist"
    track.grouping = "New Grouping"
    track.original_album = None
    track.original_artist = ["Old Original Artist"]
    track.original_title = None
    track.id3 = id3.ID3(track.file_path)

    mock_id3_instance = mock_id3_tags(
        {
            "TIT2": TIT2(encoding=3, text="Old Title"),
            "TPE1": TPE1(encoding=3, text=["Old Artist"]),
            "TALB": TALB(encoding=3, text="Old Album"),
            "TPE2": TPE2(encoding=3, text="Old Album Artist"),
            "TIT1": TIT1(encoding=3, text="Old Grouping"),
            "TOAL": TOAL(encoding=3, text="Old Original Album"),
            "TOPE": TOPE(encoding=3, text=["Old Original Artist"]),
            "TPE3": TPE3(encoding=3, text="Old Original Title"),
        }
    )

    # Act
    track.save_file_metadata()

    # Assert
    expected_setitem_calls = [
        call("TIT2", TIT2(encoding=3, text="New Title")),
        call("TPE1", TPE1(encoding=3, text="New Artist")),
        call("TALB", TALB(encoding=3, text="New Album")),
        call("TIT1", TIT1(encoding=3, text="New Grouping")),
    ]
    expected_pop_calls = [call("TOAL", None), call("TPE3", None)]

    mock_id3_instance.__setitem__.assert_has_calls(
        expected_setitem_calls, any_order=True
    )
    mock_id3_instance.pop.assert_has_calls(expected_pop_calls, any_order=True)
    mock_id3_instance.save.assert_called_once()


@pytest.mark.asyncio
async def test_formatted_new_artist_multiple_artists():
    # Arrange
    manager = TrackManager()
    track = TrackDetails("/fake/path/file1.mp3", manager)

    artist1 = MbArtistDetails(
        name="Artist1",
        type="Person",
        disambiguation="",
        sort_name="Artist1, Firstname",
        id="mock-artist1-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )
    artist1.custom_name = "Custom Artist1"
    artist1.include = True

    artist2 = MbArtistDetails(
        name="Artist2",
        type="character",
        disambiguation="",
        sort_name="Artist2, Firstname",
        id="mock-artist2-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )
    artist2.custom_name = "Custom Character2"
    artist2.include = True

    artist3 = MbArtistDetails(
        name="Artist3",
        type="group",
        disambiguation="",
        sort_name="Artist3, Firstname",
        id="mock-artist3-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )
    artist3.custom_name = "Custom Group3"
    artist3.include = False  # This artist should be excluded

    track.artist_details = [artist1, artist2, artist3]

    # Act
    concatenated_string = track.formatted_new_artist

    # Assert
    assert (
        concatenated_string == "Custom Artist1; (Custom Character2)"
    ), "Failed to concatenate artist details correctly"


@pytest.mark.asyncio
async def test_formatted_new_artist_empty():
    # Arrange
    manager = TrackManager()
    track = TrackDetails("/fake/path/file2.mp3", manager)
    track.artist_details = []

    # Act
    concatenated_string = track.formatted_new_artist

    # Assert
    assert (
        concatenated_string == ""
    ), "Failed to handle empty artist details list correctly"


@pytest.mark.asyncio
async def test_save_files_mixed_update_file_property(mocker):
    # Arrange
    manager = TrackManager()

    # Create mock TrackDetails with mixed update_file values
    track1 = create_mock_trackdetails()
    track2 = create_mock_trackdetails()
    track1.update_file = True
    track2.update_file = False
    manager.tracks = [track1, track2]

    # Mock apply_custom_tag_values and save_file_metadata methods
    mocker.patch.object(track1, "apply_custom_tag_values", new_callable=MagicMock)
    mocker.patch.object(track2, "apply_custom_tag_values", new_callable=MagicMock)
    mocker.patch.object(track1, "save_file_metadata", new_callable=AsyncMock)
    mocker.patch.object(track2, "save_file_metadata", new_callable=AsyncMock)

    # Act
    await manager.save_files()

    # Assert
    track1.apply_custom_tag_values.assert_called_once()
    track2.apply_custom_tag_values.assert_not_called()
    track1.save_file_metadata.assert_called_once()
    track2.save_file_metadata.assert_not_called()


@pytest.mark.asyncio
async def test_replace_original_title_overwrite_true():
    # Arrange
    manager = TrackManager()
    track1 = create_mock_trackdetails()
    track2 = create_mock_trackdetails()
    track1.title = "New Title 1"
    track1.original_title = "Old Title 1"
    track2.title = "New Title 2"
    track2.original_title = None
    manager.tracks = [track1, track2]

    # Act
    manager.replace_original_title(overwrite=True)

    # Assert
    assert (
        track1.original_title == "New Title 1"
    ), "Failed to overwrite original_title when overwrite=True"
    assert (
        track2.original_title == "New Title 2"
    ), "Failed to set original_title when overwrite=True and original_title is None"


@pytest.mark.asyncio
async def test_replace_original_title_overwrite_false():
    # Arrange
    manager = TrackManager()
    track1 = create_mock_trackdetails()
    track2 = create_mock_trackdetails()
    track1.title = "New Title 1"
    track1.original_title = "Old Title 1"
    track2.title = "New Title 2"
    track2.original_title = None
    manager.tracks = [track1, track2]

    # Act
    manager.replace_original_title(overwrite=False)

    # Assert
    assert (
        track1.original_title == "Old Title 1"
    ), "Unexpectedly overwrote original_title when overwrite=False"
    assert (
        track2.original_title == "New Title 2"
    ), "Failed to set original_title when overwrite=False and original_title is None"


@pytest.mark.asyncio
async def test_replace_original_artist_overwrite_true():
    # Arrange
    manager = TrackManager()
    track1 = create_mock_trackdetails()
    track2 = create_mock_trackdetails()
    track1.artist = ["New Artist 1"]
    track1.original_artist = ["Old Artist 1"]
    track2.artist = ["New Artist 2"]
    track2.original_artist = None
    manager.tracks = [track1, track2]

    # Act
    manager.replace_original_artist(overwrite=True)

    # Assert
    assert track1.original_artist == [
        "New Artist 1"
    ], "Failed to overwrite original_artist when overwrite=True"
    assert track2.original_artist == [
        "New Artist 2"
    ], "Failed to set original_artist when overwrite=True and original_artist is None"


@pytest.mark.asyncio
async def test_replace_original_artist_overwrite_false():
    # Arrange
    manager = TrackManager()
    track1 = create_mock_trackdetails()
    track2 = create_mock_trackdetails()
    track1.artist = ["New Artist 1"]
    track1.original_artist = ["Old Artist 1"]
    track2.artist = ["New Artist 2"]
    track2.original_artist = None
    manager.tracks = [track1, track2]

    # Act
    manager.replace_original_artist(overwrite=False)

    # Assert
    assert track1.original_artist == [
        "Old Artist 1"
    ], "Unexpectedly overwrote original_artist when overwrite=False"
    assert track2.original_artist == [
        "New Artist 2"
    ], "Failed to set original_artist when overwrite=False and original_artist is None"


@pytest.mark.asyncio
async def test_remove_track():
    # Arrange
    manager = TrackManager()

    artist1 = MbArtistDetails(
        name="Artist1",
        type="Person",
        disambiguation="",
        sort_name="Artist1, Firstname",
        id="mock-artist1-id",
        aliases=[],
        type_id="type-id-1",
        joinphrase="",
    )

    artist2 = MbArtistDetails(
        name="Artist2",
        type="Person",
        disambiguation="",
        sort_name="Artist2, Firstname",
        id="mock-artist2-id",
        aliases=[],
        type_id="type-id-2",
        joinphrase="",
    )

    artist3 = MbArtistDetails(
        name="Artist3",
        type="Person",
        disambiguation="",
        sort_name="Artist3, Firstname",
        id="mock-artist3-id",
        aliases=[],
        type_id="type-id-3",
        joinphrase="",
    )

    track1 = create_mock_trackdetails()
    track2 = create_mock_trackdetails()
    track3 = create_mock_trackdetails()

    track1.artist_details = [artist1]
    track2.artist_details = [artist2]
    track3.artist_details = [artist1, artist3]

    manager.tracks = [track1, track2, track3]

    # Populate artist_data manually for this test
    manager.artist_data = {
        artist1.id: artist1,
        artist2.id: artist2,
        artist3.id: artist3,
    }

    # Act
    manager.remove_track(track1)

    # Assert
    assert len(manager.tracks) == 2
    assert track1 not in manager.tracks
    assert "mock-artist1-id" in manager.artist_data
    assert "mock-artist2-id" in manager.artist_data
    assert "mock-artist3-id" in manager.artist_data

    manager.remove_track(track3)

    assert len(manager.tracks) == 1
    assert track3 not in manager.tracks
    assert "mock-artist1-id" not in manager.artist_data
    assert "mock-artist2-id" in manager.artist_data
    assert "mock-artist3-id" not in manager.artist_data

    manager.remove_track(track2)

    assert len(manager.tracks) == 0
    assert track2 not in manager.tracks
    assert "mock-artist2-id" not in manager.artist_data


@pytest.mark.asyncio
async def test_remove_track_no_remaining_references():
    # Arrange
    manager = TrackManager()

    artist1 = MbArtistDetails(
        name="Artist1",
        type="Person",
        disambiguation="",
        sort_name="Artist1, Firstname",
        id="mock-artist1-id",
        aliases=[],
        type_id="type-id-1",
        joinphrase="",
    )

    artist2 = MbArtistDetails(
        name="Artist2",
        type="Person",
        disambiguation="",
        sort_name="Artist2, Firstname",
        id="mock-artist2-id",
        aliases=[],
        type_id="type-id-2",
        joinphrase="",
    )

    track1 = create_mock_trackdetails()
    track2 = create_mock_trackdetails()

    track1.artist_details = [artist1, artist2]
    track2.artist_details = [artist1]

    manager.tracks = [track1, track2]

    # Populate artist_data manually for this test
    manager.artist_data = {
        "mock-artist1-id": artist1,
        "mock-artist2-id": artist2,
    }

    # Act
    manager.remove_track(track1)

    # Assert
    assert len(manager.tracks) == 1
    assert track1 not in manager.tracks
    assert "mock-artist1-id" in manager.artist_data
    assert "mock-artist2-id" not in manager.artist_data

    manager.remove_track(track2)

    assert len(manager.tracks) == 0
    assert track2 not in manager.tracks
    assert "mock-artist1-id" not in manager.artist_data


@pytest.mark.asyncio
async def test_load_files_valid_files(mocker):
    # Arrange
    files = ["/fake/path/file1.mp3", "/fake/path/file2.mp3", "/fake/path/file3.mp3"]
    manager = TrackManager()

    # Mock read_files to be an awaitable that does nothing
    mocker.patch.object(manager, "read_files", new_callable=AsyncMock)

    # Act
    await manager.load_files(files)

    # Assert
    manager.read_files.assert_awaited_once()
    assert len(manager.tracks) == len(files)
    for i in range(len(files)):
        assert os.path.normpath(manager.tracks[i].file_path) == os.path.normpath(
            files[i]
        )


@pytest.mark.asyncio
async def test_load_files_duplicate_files(mocker):
    # Arrange
    file1 = ["/fake/path/file1.mp3"]
    file2 = ["/fake/path/file2.mp3"]
    manager = TrackManager()

    # Mock read_files to be an awaitable that does nothing
    mocker.patch.object(manager, "read_files", new_callable=AsyncMock)

    # Act
    await manager.load_files(file1)
    await manager.load_files(file2)

    # Assert
    await manager.load_files(file1)

    assert len(manager.tracks) == 2


@pytest.mark.asyncio
async def test_load_files_invalid_file_extension():
    # Arrange
    files = [
        "/fake/path/file1.mp3",
        "/fake/path/file2.ogg",  # Invalid file extension
        "/fake/path/file3.mp3",
    ]
    manager = TrackManager()

    # Act & Assert
    with pytest.raises(
        ValueError,
        match="Invalid file type for /fake/path/file2.ogg. Only MP3 files are allowed.",
    ):
        await manager.load_files(files)


@pytest.mark.skipif(
    sys.platform != "win32", reason="Test is specific to windows file path handling"
)
@pytest.mark.asyncio
async def test_load_files_with_path_normalization(mocker):
    # this is mostly relevant for cross-os compatibility
    # Arrange
    files = [
        os.path.normpath("C:/fake/path/file1.mp3"),
        os.path.normpath("C:\\fake\\path\\file1.mp3"),
    ]
    manager = TrackManager()

    # Mock read_files to be an awaitable that does nothing
    mocker.patch.object(manager, "read_files", new_callable=AsyncMock)

    # Act
    await manager.load_files(files)

    # Assert
    manager.read_files.assert_awaited_once()
    assert len(manager.tracks) == 1
    assert os.path.normpath(manager.tracks[0].file_path) == os.path.normpath(files[0])


@pytest.mark.asyncio
async def test_load_files_with_mixed_slashes(mocker):
    # Arrange
    files = [
        "/fake/path/file1.mp3",
        "\\fake\\path\\file2.mp3",
        "C:/fake/path\\file3.mp3",
    ]
    manager = TrackManager()

    # Mock read_files to be an awaitable that does nothing
    mocker.patch.object(manager, "read_files", new_callable=AsyncMock)

    # Act
    await manager.load_files(files)

    # Assert
    manager.read_files.assert_awaited_once()
    assert len(manager.tracks) == len(files)
    for i in range(len(files)):
        assert os.path.normpath(manager.tracks[i].file_path) == os.path.normpath(
            files[i]
        )


@pytest.mark.asyncio
async def test_formatted_artist():
    # Arrange
    manager = TrackManager()
    track = TrackDetails("/fake/path/file1.mp3", manager)
    track.artist = ["Artist1", "Artist2"]

    # Act
    formatted_artist = track.formatted_artist

    # Assert
    assert (
        formatted_artist == "Artist1; Artist2"
    ), "Failed to concatenate artist names correctly"

    # Test case with no artists
    track.artist = []
    formatted_artist = track.formatted_artist
    assert formatted_artist == "", "Failed to handle empty artist list correctly"

    # Test case with a single artist
    track.artist = ["Single Artist"]
    formatted_artist = track.formatted_artist
    assert (
        formatted_artist == "Single Artist"
    ), "Failed to handle single artist correctly"


@pytest.mark.skip(reason="integration test, only called manually")
@pytest.mark.asyncio
async def test_txxx_delete_artist_relations_frame():
    # not really a unit test since it needs a specific file to exist
    # to verify that the actual mutagen tags work, but it's handy to keep around
    # Arrange
    file_path = "C:/Users/email_000/Desktop/music/check.mp3"

    manager = TrackManager()

    # Act
    # Load the file
    await manager.load_files([file_path])

    # Check if file was loaded correctly
    track = manager.tracks[0]

    # Update artist info from the database
    await manager.update_artists_info_from_db()

    # Clear the artist_relations value to simulate deletion by user
    track.artist_relations = None

    # Save the file metadata
    # track.save_file_metadata()

    # Reload the file to verify the frame was deleted
    await manager.load_files([file_path])
    track = manager.tracks[0]

    # Assert
    artist_relations_frame = next(
        (
            frame
            for frame in track.id3.getall("TXXX")
            if frame.desc == "artist_relations_json"
        ),
        None,
    )

    assert (
        artist_relations_frame is None
    ), "The artist_relations_json frame should be deleted"
