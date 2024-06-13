import pytest
import httpx
import respx
import json
from mutagen.id3 import TXXX
from artist_resolver.trackmanager import (
    MbArtistDetails,
    TrackDetails,
    TrackManager,
    SimpleArtistDetails,
)


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
async def test_create_mbartist_objects_without_db_information(respx_mock):
    # Arrange
    manager = TrackManager()

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

    artist2 = MbArtistDetails(
        name="Artist2",
        type="Person",
        disambiguation="",
        sort_name="Artist2, Firstname",
        id="mock-artist2-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )

    # Populate artist_data with MbArtistDetails
    manager.artist_data[artist1.mbid] = artist1
    manager.artist_data[artist2.mbid] = artist2

    # Mock the DB call to always return 404
    respx_mock.route(
        method="GET",
        port__in=[manager.api_port],
        host=manager.api_host,
        path__regex=r"/api/mbartist/mbid/.*",
    ).mock(return_value=httpx.Response(404))

    # Add a catch-all for everything that's not explicitly routed
    # respx_mock.route().respond(404)

    # Act
    await manager.update_artists_info_from_db()

    # Assert
    assert manager.artist_data[artist1.mbid].custom_name == "Artist1 Firstname"
    assert manager.artist_data[artist2.mbid].custom_name == "Artist2 Firstname"
    assert manager.artist_data[artist1.mbid].custom_original_name == artist1.name
    assert manager.artist_data[artist2.mbid].custom_original_name == artist2.name
    assert manager.artist_data[artist1.mbid].include == artist1.include
    assert manager.artist_data[artist2.mbid].include == artist2.include
    assert manager.artist_data[artist1.mbid].type == artist1.type
    assert manager.artist_data[artist2.mbid].type == artist2.type


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_create_mbartist_objects_with_db_information(respx_mock):
    # Arrange
    manager = TrackManager()

    artist1 = MbArtistDetails(
        name="Artist1 Lastname",
        type="Person",
        disambiguation="",
        sort_name="Lastname, Artist1",
        id="mock-artist1-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )

    artist1_expected = {
        "id": 239,
        "mbid": "mock-artist1-id",
        "type": "Character",
        "custom_name": "Expected Lastname Artist1",
        "custom_original_name": "Expected Lastname Artist1 Original",
        "include": False,
    }

    # Populate artist_data with MbArtistDetails
    manager.artist_data[artist1.mbid] = artist1

    # Mock the DB call to return 200 for the specified mbid
    respx_mock.route(
        method="GET",
        port__in=[manager.api_port],
        host=manager.api_host,
        path=f"/api/mbartist/mbid/mock-artist1-id",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": artist1_expected["id"],
                "mbid": artist1_expected["mbid"],
                "name": artist1_expected["custom_name"],
                "type": artist1_expected["type"],
                "originalName": artist1_expected["custom_original_name"],
                "include": artist1_expected["include"],
            },
        )
    )

    # Act
    await manager.update_artists_info_from_db()

    # Assert
    assert manager.artist_data[artist1.mbid].id == artist1_expected["id"]
    assert manager.artist_data[artist1.mbid].mbid == artist1_expected["mbid"]
    assert (
        manager.artist_data[artist1.mbid].custom_name == artist1_expected["custom_name"]
    )
    assert (
        manager.artist_data[artist1.mbid].custom_original_name
        == artist1_expected["custom_original_name"]
    )
    assert manager.artist_data[artist1.mbid].include == artist1_expected["include"]
    assert manager.artist_data[artist1.mbid].type == artist1_expected["type"]


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_mbid_not_found_in_db_when_saving(respx_mock):
    # Arrange
    manager = TrackManager()

    server_artist_id = 35

    artist = MbArtistDetails(
        name="NewSimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="NewSimpleArtist",
        id=None,
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )

    artist.mbid = "mock-artist1-id"
    artist.include = False
    artist.custom_name = "New custom name"
    artist.custom_original_name = "New custom original name"
    manager.artist_data[artist.mbid] = artist

    # Mock first request to not return anything when checking artist by name
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist/mbid/{artist.mbid}",
    ).mock(return_value=httpx.Response(404))

    # Mock call to update artist
    respx_mock.route(
        method="POST",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": server_artist_id,
                "mbId": artist.mbid,
                "name": artist.custom_name,
                "type": artist.type,
                "originalName": artist.custom_original_name,
                "include": artist.include,
            },
        )
    )

    # Act
    await manager.send_mbartist_changes_to_db(artist)

    # Assert
    assert respx_mock.calls.call_count == 2

    # verify if artist exists
    assert (
        respx_mock.calls[0].request.method == "GET"
    ), "Call to verify if an artist exist was not of type GET"

    # post new artist
    assert (
        respx_mock.calls[1].request.method == "POST"
    ), "Call to update artist was not of type UPDATE"
    call_1_content = json.loads(respx_mock.calls[1].request.content.decode())
    assert call_1_content == {
        "MbId": artist.mbid,
        "Name": artist.custom_name,
        "Type": artist.type,
        "OriginalName": artist.custom_original_name,
        "Include": artist.include,
    }, f"Post body to update artist did not match expected object"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_mbid_found_on_server_when_saving_data_identical(respx_mock):
    # Arrange
    manager = TrackManager()

    server_artist_name = "New custom name"
    server_artist_id = 35

    artist = MbArtistDetails(
        name="NewSimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="NewSimpleArtist",
        id=None,
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )

    artist.mbid = "mock-artist1-id"
    artist.include = True
    artist.custom_name = server_artist_name
    artist.custom_original_name = "New custom original name"
    manager.artist_data[artist.mbid] = artist

    # Mock first request to not return anything when checking artist by name
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist/mbid/{artist.mbid}",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": server_artist_id,
                "mbId": artist.mbid,
                "type": artist.type,
                "name": server_artist_name,
                "originalName": artist.custom_original_name,
                "include": artist.include,
            },
        )
    )

    # Act
    await manager.send_mbartist_changes_to_db(artist)

    # Assert
    assert respx_mock.calls.call_count == 1

    # verify if artist exists
    assert (
        respx_mock.calls[0].request.method == "GET"
    ), "Call to verify if an artist exist was not of type GET"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_mbid_found_on_server_when_saving_data_changed(respx_mock):
    # Arrange
    manager = TrackManager()

    server_artist_name = "ServerCustomName"
    server_artist_type = "Character"
    server_artist_id = 35

    artist = MbArtistDetails(
        name="NewSimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="NewSimpleArtist",
        id=None,
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )

    artist.mbid = "mock-artist1-id"
    artist.include = True
    artist.custom_name = "New custom name"
    artist.custom_original_name = "New custom original name"
    manager.artist_data[artist.mbid] = artist

    # Mock first request to not return anything when checking artist by name
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist/mbid/{artist.mbid}",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": server_artist_id,
                "mbId": artist.mbid,
                "name": server_artist_name,
                "type": server_artist_type,
                "originalName": artist.custom_original_name,
                "include": artist.include,
            },
        )
    )

    # Mock call to update artist
    respx_mock.route(
        method="PUT",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist/id/{server_artist_id}",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": artist.id,
                "mbId": artist.mbid,
                "name": artist.custom_name,
                "type": artist.type,
                "originalName": artist.custom_original_name,
                "include": artist.include,
            },
        )
    )

    # Act
    await manager.send_mbartist_changes_to_db(artist)

    # Assert
    assert respx_mock.calls.call_count == 2

    # verify if artist exists
    assert (
        respx_mock.calls[0].request.method == "GET"
    ), "Call to verify if an artist exist was not of type GET"

    # post new artist
    assert (
        respx_mock.calls[1].request.method == "PUT"
    ), "Call to update artist was not of type UPDATE"
    call_1_content = json.loads(respx_mock.calls[1].request.content.decode())
    assert call_1_content == {
        "MbId": artist.mbid,
        "Name": artist.custom_name,
        "Type": artist.type,
        "OriginalName": artist.custom_original_name,
        "Include": artist.include,
    }, f"Post body to update artist did not match expected object"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_update_from_customization_sets_has_server_data(respx_mock):
    # Arrange
    manager = TrackManager()

    artist = MbArtistDetails(
        name="MbArtist",
        type="Person",
        disambiguation="",
        sort_name="MbArtist",
        id="mock-artist-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )

    manager.artist_data[artist.mbid] = artist

    # Mock the DB call to return artist data
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist/mbid/{artist.mbid}",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 1,
                "mbid": "mock-artist-id",
                "name": "UpdatedMbArtist",
                "originalName": "MbArtist",
                "type": "Person",
                "include": True,
            },
        )
    )

    # Act
    await manager.update_artists_info_from_db()

    # Assert
    assert artist.has_server_data, "Expected artist.has_server_data to be True"


@pytest.mark.asyncio
async def test_formatted_artist():
    # Test case where custom_name is not None or empty
    artist = MbArtistDetails(
        name="Original Artist",
        type="Person",
        disambiguation="",
        sort_name="Original Artist",
        id="mock-id-1",
        aliases=[],
        type_id="type-id-1",
        joinphrase="",
    )
    artist.custom_name = "Custom Artist"
    assert artist.formatted_artist == "Custom Artist", "Failed when custom_name is set"

    # Test case where custom_name is None
    artist.custom_name = None
    assert (
        artist.formatted_artist == "Original Artist"
    ), "Failed when custom_name is None"

    # Test case where custom_name is empty
    artist.custom_name = ""
    assert (
        artist.formatted_artist == "Original Artist"
    ), "Failed when custom_name is empty"

    # Test case where type is "character"
    artist.type = "character"
    artist.custom_name = "Custom Character"
    assert (
        artist.formatted_artist == "(Custom Character)"
    ), "Failed when type is 'character'"

    # Test case where type is "group"
    artist.type = "group"
    artist.custom_name = "Custom Group"
    assert artist.formatted_artist == "(Custom Group)", "Failed when type is 'group'"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_create_track_file_with_artist_json(mock_id3_tags):
    # Arrange1
    reference_track = create_mock_trackdetails()
    reference_track.product = None

    mbid = "mock-93fb-4bc3-8ff9-065c75c4f90a"

    mock_id3_tags(
        {
            "TIT2": reference_track.title,
            "TPE1": reference_track.artist,
            "TALB": reference_track.album,
            "TPE2": reference_track.album_artist,
            "TIT1": reference_track.grouping,
            "TOAL": reference_track.original_album,
            "TOPE": reference_track.original_artist,
            "TPE3": reference_track.original_title,
        },
        txxx_frames=[
            TXXX(
                encoding=3,
                HashKey="TXXX:artist_relations_json",
                desc="artist_relations_json",
                text=[
                    json.dumps(
                        [
                            {
                                "name": "Firstname Lastname",
                                "type": "Person",
                                "disambiguation": "",
                                "sort_name": "Lastname, Firstname",
                                "id": mbid,
                                "aliases": [],
                                "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
                                "relations": [],
                                "joinphrase": "",
                            }
                        ]
                    )
                ],
            )
        ],
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
    assert track.product == reference_track.product


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_parse_artist_json_with_nested_objects():
    # Arrange

    input_object = [
        {
            "name": "Character1 Lastname",
            "type": "Character",
            "disambiguation": "Mock Franchise1",
            "sort_name": "Lastname, Character1",
            "id": "mock-e7a3-42ac-a08c-3aa896f87bd5",
            "aliases": [],
            "type_id": "5c1375b0-f18d-3db7-a164-a49d7a63773f",
            "relations": [
                {
                    "name": "Person1 Lastname",
                    "type": "Person",
                    "disambiguation": "",
                    "sort_name": "Lastname, Person1",
                    "id": "mock-d84a-4523-b45c-de3348e968fd",
                    "aliases": [
                        {
                            "locale": "en",
                            "name": "Person1AliasEn Lastname",
                            "type-id": "894afba6-2816-3c24-8072-eadb66bd04bc",
                            "begin": "null",
                            "primary": "true",
                            "end": "null",
                            "sort-name": "Lastname, Person1AliasEn",
                            "ended": "false",
                            "type": "Artist name",
                        },
                        {
                            "end": "null",
                            "locale": "ja",
                            "name": "Person1AliasJa Lastname",
                            "type-id": "mock-d8f4-4ea6-85a2-cf649203489b",
                            "begin": "null",
                            "primary": "true",
                            "sort-name": "Lastname, Person1AliasJa",
                            "ended": "false",
                            "type": "Artist name",
                        },
                    ],
                    "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
                    "relations": [],
                    "joinphrase": "",
                }
            ],
            "joinphrase": "(CV.",
        },
        {
            "name": "Person1 Lastname",
            "type": "Person",
            "disambiguation": "",
            "sort_name": "Lastname, Person1",
            "id": "mock-d84a-4523-b45c-de3348e968fd",
            "aliases": [
                {
                    "locale": "en",
                    "name": "Person1AliasEn Lastname",
                    "type-id": "894afba6-2816-3c24-8072-eadb66bd04bc",
                    "begin": "null",
                    "primary": "true",
                    "end": "null",
                    "sort-name": "Lastname, Person1AliasEn",
                    "ended": "false",
                    "type": "Artist name",
                },
                {
                    "end": "null",
                    "locale": "ja",
                    "name": "Person1AliasJa Lastname",
                    "type-id": "mock-d8f4-4ea6-85a2-cf649203489b",
                    "begin": "null",
                    "primary": "true",
                    "sort-name": "Lastname, Person1AliasJa",
                    "ended": "false",
                    "type": "Artist name",
                },
            ],
            "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
            "relations": [],
            "joinphrase": ")、",
        },
        {
            "name": "Character2 Lastname",
            "type": "Character",
            "disambiguation": "Mock Franchise2",
            "sort_name": "Lastname, Character2",
            "id": "mock-3e63-42a5-8251-4dbe07ebc9e2",
            "aliases": [],
            "type_id": "5c1375b0-f18d-3db7-a164-a49d7a63773f",
            "relations": [
                {
                    "name": "Person3 Lastname",
                    "type": "Person",
                    "disambiguation": "",
                    "sort_name": "Lastname, Person3",
                    "id": "mock-12da-42b2-9fae-3c93b9a3bcdb",
                    "aliases": [],
                    "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
                    "relations": [],
                }
            ],
            "joinphrase": "(CV.",
        },
        {
            "name": "Person3 Lastname",
            "type": "Person",
            "disambiguation": "",
            "sort_name": "Lastname, Person3",
            "id": "mock-12da-42b2-9fae-3c93b9a3bcdb",
            "aliases": [],
            "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
            "relations": [],
            "joinphrase": ")",
        },
    ]

    expected_character1 = {
        "name": "Character1 Lastname",
        "type": "Character",
        "disambiguation": "Mock Franchise1",
        "sort_name": "Lastname, Character1",
        "id": "mock-e7a3-42ac-a08c-3aa896f87bd5",
        "aliases": [],
        "type_id": "5c1375b0-f18d-3db7-a164-a49d7a63773f",
        "relations": [
            {
                "name": "Person1 Lastname",
                "type": "Person",
                "disambiguation": "",
                "sort_name": "Lastname, Person1",
                "id": "mock-d84a-4523-b45c-de3348e968fd",
                "aliases": [
                    {
                        "locale": "en",
                        "name": "Person1AliasEn Lastname",
                        "type-id": "894afba6-2816-3c24-8072-eadb66bd04bc",
                        "begin": "null",
                        "primary": "true",
                        "end": "null",
                        "sort-name": "Lastname, Person1AliasEn",
                        "ended": "false",
                        "type": "Artist name",
                    },
                    {
                        "end": "null",
                        "locale": "ja",
                        "name": "Person1AliasJa Lastname",
                        "type-id": "mock-d8f4-4ea6-85a2-cf649203489b",
                        "begin": "null",
                        "primary": "true",
                        "sort-name": "Lastname, Person1AliasJa",
                        "ended": "false",
                        "type": "Artist name",
                    },
                ],
                "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
                "relations": [],
                "joinphrase": "",
            }
        ],
        "joinphrase": "(CV.",
    }

    expected_character2 = {
        "name": "Character2 Lastname",
        "type": "Character",
        "disambiguation": "Mock Franchise2",
        "sort_name": "Lastname, Character2",
        "id": "mock-3e63-42a5-8251-4dbe07ebc9e2",
        "aliases": [],
        "type_id": "5c1375b0-f18d-3db7-a164-a49d7a63773f",
        "relations": [],
        "joinphrase": "(CV.",
    }

    expected_person1 = {
        "name": "Person1 Lastname",
        "type": "Person",
        "disambiguation": "",
        "sort_name": "Lastname, Person1",
        "id": "mock-d84a-4523-b45c-de3348e968fd",
        "aliases": [
            {
                "locale": "en",
                "name": "Person1AliasEn Lastname",
                "type-id": "894afba6-2816-3c24-8072-eadb66bd04bc",
                "begin": "null",
                "primary": "true",
                "end": "null",
                "sort-name": "Lastname, Person1AliasEn",
                "ended": "false",
                "type": "Artist name",
            },
            {
                "end": "null",
                "locale": "ja",
                "name": "Person1AliasJa Lastname",
                "type-id": "mock-d8f4-4ea6-85a2-cf649203489b",
                "begin": "null",
                "primary": "true",
                "sort-name": "Lastname, Person1AliasJa",
                "ended": "false",
                "type": "Artist name",
            },
        ],
        "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
        "relations": [],
        "joinphrase": ")、",
    }

    expected_person3 = {
        "name": "Person3 Lastname",
        "type": "Person",
        "disambiguation": "",
        "sort_name": "Lastname, Person3",
        "id": "mock-12da-42b2-9fae-3c93b9a3bcdb",
        "aliases": [],
        "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
        "relations": [],
        "joinphrase": ")",
    }

    # the json object will be deduplicated and flattened, which is why it looks different from the expected list
    expected = [
        expected_person1,
        expected_character1,
        expected_person3,
        expected_character2,
    ]

    # Act
    artist_relation_cache = MbArtistDetails.build_artist_relation_cache(
        input_object, {}, None, None
    )
    sorted_data = MbArtistDetails.sort_artist_json(artist_relation_cache, None)
    flattened_data = MbArtistDetails.flatten_artist_json(sorted_data)

    # Assert
    assert len(flattened_data) == 4, f"Unexpected number of entries"

    for i in range(len(expected)):
        expected_artist = expected[i]
        actual_artist = flattened_data[i]
        assert actual_artist["id"] == expected_artist["id"], f"ID mismatch at index {i}"
        assert (
            actual_artist["name"] == expected_artist["name"]
        ), f"name mismatch at index {i}"
        assert (
            actual_artist["sort_name"] == expected_artist["sort_name"]
        ), f"sort_name mismatch at index {i}"
        assert (
            actual_artist["type"] == expected_artist["type"]
        ), f"type mismatch at index {i}"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_parse_artist_json_with_nested_objects2():
    # Arrange

    input_object = [
        {
            "name": "Group 1",
            "type": "Group",
            "disambiguation": "",
            "sort_name": "Group 1",
            "id": "mock-e7a3-4673-a08c-26a996f87bd5",
            "aliases": [],
            "type_id": "e431f5f6-b5d2-343d-8b36-72607fffb74b",
            "joinphrase": "",
            "relations": [
                {
                    "name": "Character1 Lastname",
                    "type": "Character",
                    "disambiguation": "",
                    "sort_name": "Lastname, Character1",
                    "id": "mock-0abd-4673-aa68-87b1fa70047c",
                    "aliases": [],
                    "type_id": "5c1375b0-f18d-3db7-a164-a49d7a63773f",
                    "joinphrase": "",
                    "relations": [
                        {
                            "name": "Person1 Lastname",
                            "type": "Person",
                            "disambiguation": "voice actor",
                            "sort_name": "Lastname, Person1",
                            "id": "mock-6193-496e-8e10-8a38960cc8ed",
                            "aliases": [],
                            "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
                            "joinphrase": "",
                            "relations": [],
                        }
                    ],
                },
                {
                    "name": "Character2 Lastname",
                    "type": "Character",
                    "disambiguation": "",
                    "sort_name": "Lastname, Character2",
                    "id": "mock-6759-4648-b777-08d15f18dbbdd",
                    "aliases": [],
                    "type_id": "5c1375b0-f18d-3db7-a164-a49d7a63773f",
                    "joinphrase": "",
                    "relations": [
                        {
                            "name": "Person2 Lastname",
                            "type": "Person",
                            "disambiguation": "voice actor",
                            "sort_name": "Lastname, Person2",
                            "id": "mock-2cb2-4080-9a3d-d327525a4e3a",
                            "aliases": [],
                            "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
                            "joinphrase": "",
                            "relations": [],
                        }
                    ],
                },
                {
                    "name": "Person2 Lastname",
                    "type": "Person",
                    "disambiguation": "voice actor",
                    "sort_name": "Lastname, Person2",
                    "id": "mock-2cb2-4080-9a3d-d327525a4e3a",
                    "aliases": [],
                    "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
                    "joinphrase": "",
                    "relations": [],
                },
                {
                    "name": "Person1 Lastname",
                    "type": "Person",
                    "disambiguation": "voice actor",
                    "sort_name": "Lastname, Person1",
                    "id": "mock-6193-496e-8e10-8a38960cc8ed",
                    "aliases": [],
                    "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
                    "joinphrase": "",
                    "relations": [],
                },
            ],
            "joinphrase": "",
        }
    ]

    expected_group1 = {
        "name": "Group 1",
        "type": "Group",
        "disambiguation": "",
        "sort_name": "Group 1",
        "id": "mock-e7a3-4673-a08c-26a996f87bd5",
        "aliases": [],
        "type_id": "e431f5f6-b5d2-343d-8b36-72607fffb74b",
        "relations": [],
        "joinphrase": "",
    }

    expected_character1 = {
        "name": "Character1 Lastname",
        "type": "Character",
        "disambiguation": "",
        "sort_name": "Lastname, Character1",
        "id": "mock-0abd-4673-aa68-87b1fa70047c",
        "aliases": [],
        "type_id": "5c1375b0-f18d-3db7-a164-a49d7a63773f",
        "relations": [],
    }

    expected_character2 = {
        "name": "Character2 Lastname",
        "type": "Character",
        "disambiguation": "",
        "sort_name": "Lastname, Character2",
        "id": "mock-6759-4648-b777-08d15f18dbbdd",
        "aliases": [],
        "type_id": "5c1375b0-f18d-3db7-a164-a49d7a63773f",
        "relations": [],
    }

    expected_person1 = {
        "name": "Person1 Lastname",
        "type": "Person",
        "disambiguation": "voice actor",
        "sort_name": "Lastname, Person1",
        "id": "mock-6193-496e-8e10-8a38960cc8ed",
        "aliases": [],
        "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
        "relations": [],
    }

    expected_person2 = {
        "name": "Person2 Lastname",
        "type": "Person",
        "disambiguation": "voice actor",
        "sort_name": "Lastname, Person2",
        "id": "mock-2cb2-4080-9a3d-d327525a4e3a",
        "aliases": [],
        "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
        "relations": [],
    }

    # the json object will be deduplicated and flattened, which is why it looks different from the expected list
    expected = [
        expected_group1,
        expected_person1,
        expected_character1,
        expected_person2,
        expected_character2,
    ]

    # Act
    artist_relation_cache = MbArtistDetails.build_artist_relation_cache(
        input_object, {}, None, None
    )
    sorted_data = MbArtistDetails.sort_artist_json(artist_relation_cache, None)
    flattened_data = MbArtistDetails.flatten_artist_json(sorted_data)

    # Assert
    assert len(flattened_data) == 5, f"Unexpected number of entries"

    for i in range(len(expected)):
        expected_artist = expected[i]
        actual_artist = flattened_data[i]
        assert actual_artist["id"] == expected_artist["id"], f"ID mismatch at index {i}"
        assert (
            actual_artist["name"] == expected_artist["name"]
        ), f"name mismatch at index {i}"
        assert (
            actual_artist["sort_name"] == expected_artist["sort_name"]
        ), f"sort_name mismatch at index {i}"
        assert (
            actual_artist["type"] == expected_artist["type"]
        ), f"type mismatch at index {i}"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_parse_artist_json_with_nested_objects3():
    # Arrange

    input_object = [
        {
            "name": "Person1 Lastname",
            "type": "Person",
            "disambiguation": "voice actor",
            "sort_name": "Lastname, Person1",
            "id": "mock-6193-496e-8e10-8a38960cc8ed",
            "aliases": [],
            "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
            "joinphrase": "",
            "relations": [],
        },
        {
            "name": "Group 1",
            "type": "Group",
            "disambiguation": "",
            "sort_name": "Group 1",
            "id": "mock-e7a3-4673-a08c-26a996f87bd5",
            "aliases": [],
            "type_id": "e431f5f6-b5d2-343d-8b36-72607fffb74b",
            "joinphrase": "",
            "relations": [
                {
                    "name": "Character1 Lastname",
                    "type": "Character",
                    "disambiguation": "",
                    "sort_name": "Lastname, Character1",
                    "id": "mock-0abd-4673-aa68-87b1fa70047c",
                    "aliases": [],
                    "type_id": "5c1375b0-f18d-3db7-a164-a49d7a63773f",
                    "joinphrase": "",
                    "relations": [
                        {
                            "name": "Person1 Lastname",
                            "type": "Person",
                            "disambiguation": "voice actor",
                            "sort_name": "Lastname, Person1",
                            "id": "mock-6193-496e-8e10-8a38960cc8ed",
                            "aliases": [],
                            "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
                            "joinphrase": "",
                            "relations": [],
                        }
                    ],
                },
                {
                    "name": "Person1 Lastname",
                    "type": "Person",
                    "disambiguation": "voice actor",
                    "sort_name": "Lastname, Person1",
                    "id": "mock-6193-496e-8e10-8a38960cc8ed",
                    "aliases": [],
                    "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
                    "joinphrase": "",
                    "relations": [],
                },
            ],
            "joinphrase": "",
        },
    ]

    expected_group1 = {
        "name": "Group 1",
        "type": "Group",
        "disambiguation": "",
        "sort_name": "Group 1",
        "id": "mock-e7a3-4673-a08c-26a996f87bd5",
        "aliases": [],
        "type_id": "e431f5f6-b5d2-343d-8b36-72607fffb74b",
        "relations": [],
        "joinphrase": "",
    }

    expected_character1 = {
        "name": "Character1 Lastname",
        "type": "Character",
        "disambiguation": "",
        "sort_name": "Lastname, Character1",
        "id": "mock-0abd-4673-aa68-87b1fa70047c",
        "aliases": [],
        "type_id": "5c1375b0-f18d-3db7-a164-a49d7a63773f",
        "relations": [],
    }

    expected_person1 = {
        "name": "Person1 Lastname",
        "type": "Person",
        "disambiguation": "voice actor",
        "sort_name": "Lastname, Person1",
        "id": "mock-6193-496e-8e10-8a38960cc8ed",
        "aliases": [],
        "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
        "relations": [],
    }

    # the json object will be deduplicated and flattened, which is why it looks different from the expected list
    expected = [
        expected_group1,
        expected_person1,
        expected_character1,
    ]

    # Act
    artist_relation_cache = MbArtistDetails.build_artist_relation_cache(
        input_object, {}, None, None
    )
    sorted_data = MbArtistDetails.sort_artist_json(artist_relation_cache, None)
    flattened_data = MbArtistDetails.flatten_artist_json(sorted_data)

    # Assert
    assert len(flattened_data) == 3, f"Unexpected number of entries"

    for i in range(len(expected)):
        expected_artist = expected[i]
        actual_artist = flattened_data[i]
        assert actual_artist["id"] == expected_artist["id"], f"ID mismatch at index {i}"
        assert (
            actual_artist["name"] == expected_artist["name"]
        ), f"name mismatch at index {i}"
        assert (
            actual_artist["sort_name"] == expected_artist["sort_name"]
        ), f"sort_name mismatch at index {i}"
        assert (
            actual_artist["type"] == expected_artist["type"]
        ), f"type mismatch at index {i}"


@pytest.mark.asyncio
async def test_reorder_json_cv_artists():
    # Arrange

    character = {
        "name": "Character1 Lastname",
        "type": "Character",
        "disambiguation": "Mock Franchise1",
        "sort_name": "Lastname, Character1",
        "id": "mock-e7a3-8888-a08c-3aa888f37bd5",
        "aliases": [],
        "type_id": "5c1375b0-f18d-3db7-a164-a49d7a63773f",
        "relations": [],
        "joinphrase": "(CV.",
    }

    person = {
        "name": "Person1 Lastname",
        "type": "Person",
        "disambiguation": "",
        "sort_name": "Lastname, Person1",
        "id": "mock-d84a-9999-b45c-eef348e968fd",
        "aliases": [],
        "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
        "relations": [],
        "joinphrase": "), ",
    }

    artists = [character, person]

    # Act
    reordered_artists = MbArtistDetails.build_artist_relation_cache(artists, {})
    flattened_data = MbArtistDetails.flatten_artist_json(reordered_artists)

    # Assert
    assert (
        flattened_data[0] == "mock-d84a-9999-b45c-eef348e968fd"
    ), "Expected Person to be first after reordering"
    assert (
        flattened_data[1] == "mock-e7a3-8888-a08c-3aa888f37bd5"
    ), "Expected Character to be second after reordering"


@pytest.mark.asyncio
async def test_reorder_nested_relations_in_from_dict():
    # Arrange
    json_str = json.dumps(
        [
            {
                "name": "Group",
                "type": "Group",
                "disambiguation": "Disambig",
                "sort_name": "Group",
                "id": "group-id",
                "aliases": [],
                "type_id": "group-type-id",
                "relations": [
                    {
                        "name": "Character",
                        "type": "Character",
                        "disambiguation": "",
                        "sort_name": "Character",
                        "id": "character-id",
                        "aliases": [],
                        "type_id": "character-type-id",
                        "relations": [
                            {
                                "name": "Person",
                                "type": "Person",
                                "disambiguation": "",
                                "sort_name": "Person",
                                "id": "person-id",
                                "aliases": [],
                                "type_id": "person-type-id",
                                "relations": [],
                            }
                        ],
                        "joinphrase": "(CV.",
                    }
                ],
                "joinphrase": "",
            }
        ]
    )

    # Act
    artists = MbArtistDetails.parse_json(json_str)

    # Assert
    assert artists[0].name == "Group", "Expected first artist to be Group"
    assert artists[1].name == "Person", "Expected second artist to be Person"
    assert artists[2].name == "Character", "Expected third artist to be Character"


@pytest.mark.asyncio
async def test_reorder_nested_relations_in_from_dict2():
    # Arrange
    json_str = json.dumps(
        [
            {
                "name": "Group",
                "type": "Group",
                "disambiguation": "Disambig",
                "sort_name": "Group",
                "id": "group-id",
                "aliases": [],
                "type_id": "group-type-id",
                "relations": [
                    {
                        "name": "Character",
                        "type": "Character",
                        "disambiguation": "",
                        "sort_name": "Character",
                        "id": "character-id",
                        "aliases": [],
                        "type_id": "character-type-id",
                        "relations": [
                            {
                                "name": "Person",
                                "type": "Person",
                                "disambiguation": "",
                                "sort_name": "Person",
                                "id": "person-id",
                                "aliases": [],
                                "type_id": "person-type-id",
                                "relations": [],
                            }
                        ],
                        "joinphrase": "(CV.",
                    }
                ],
                "joinphrase": "",
            }
        ]
    )

    # Act
    artists = MbArtistDetails.parse_json(json_str)

    # Assert
    assert artists[0].name == "Group", "Expected first artist to be Group"
    assert artists[1].name == "Person", "Expected second artist to be Person"
    assert artists[2].name == "Character", "Expected third artist to be Character"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_read_file_metadata_read_artist_json_true_creates_simple_artist(
    mock_id3_tags, respx_mock
):
    # Arrange
    reference_track = create_mock_trackdetails()
    reference_track.product = None

    artist_json = json.dumps(
        [
            {
                "name": "Simple Artist",
                "type": "Person",
                "disambiguation": "",
                "sort_name": "Simple, Artist",
                "id": "simple-artist-id",
                "aliases": [],
                "type_id": "b6e035f4-3ce9-331c-97df-83397230b0df",
                "relations": [],
                "joinphrase": "",
            }
        ]
    )

    mock_id3_tags(
        {
            "TIT2": reference_track.title,
            "TPE1": reference_track.artist,
            "TALB": reference_track.album,
            "TPE2": reference_track.album_artist,
            "TIT1": reference_track.grouping,
            "TOAL": reference_track.original_album,
            "TOPE": reference_track.original_artist,
            "TPE3": reference_track.original_title,
        },
        txxx_frames=[
            TXXX(
                encoding=3,
                HashKey="TXXX:artist_relations_json",
                desc="artist_relations_json",
                text=[artist_json],
            )
        ],
    )

    simpleartist_manager = TrackManager()

    respx_mock.route(
        method="GET",
        port__in=[simpleartist_manager.api_port],
        host=simpleartist_manager.api_host,
        path="/api/franchise",
    ).mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": 1, "name": "_", "aliases": []},
            ],
        )
    )

    # Act
    mbartist_manager = TrackManager()
    mbartist_track = TrackDetails("/fake/path/file1.mp3", mbartist_manager)
    await mbartist_track.read_file_metadata(read_artist_json=True)

    simpleartist_track = TrackDetails("/fake/path/file1.mp3", simpleartist_manager)
    await simpleartist_track.read_file_metadata(read_artist_json=False)

    # Assert
    assert all(
        isinstance(artist, MbArtistDetails)
        for artist in mbartist_manager.artist_data.values()
    )
    assert all(
        isinstance(artist, MbArtistDetails) for artist in mbartist_track.artist_details
    )

    assert all(
        isinstance(artist, SimpleArtistDetails)
        for artist in simpleartist_manager.artist_data.values()
    )
    assert all(
        isinstance(artist, SimpleArtistDetails)
        for artist in simpleartist_track.artist_details
    )
