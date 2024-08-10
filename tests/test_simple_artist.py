import hashlib
import pytest
import httpx
import respx
import json
from artist_resolver.trackmanager import (
    SimpleArtistDetails,
    TrackManager,
    TrackDetails,
)


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_create_artist_objects_with_unknown_alias(respx_mock):
    # Arrange
    manager = TrackManager()

    artist1 = SimpleArtistDetails(
        name="SimpleArtist1",
        type="Person",
        disambiguation="",
        sort_name="SimpleArtist1",
        id="mock-artist1-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="TestProduct",
        product_id="1",
    )

    artist2 = SimpleArtistDetails(
        name="SimpleArtist2",
        type="Person",
        disambiguation="",
        sort_name="SimpleArtist2",
        id="mock-artist2-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="TestProduct",
        product_id="2",
    )

    # Populate artist_data with SimpleArtistDetails
    manager.artist_data[artist1.mbid] = artist1
    manager.artist_data[artist2.mbid] = artist2

    # Mock the DB call to return an empty object
    respx_mock.route(
        method="GET",
        port__in=[manager.api_port],
        host=manager.api_host,
        path__regex=r"/api/alias.*",
    ).mock(return_value=httpx.Response(200, text="[]"))

    # Act
    await manager.update_artists_info_from_db()

    # Assert
    assert manager.artist_data[artist1.mbid].custom_name == artist1.sort_name
    assert manager.artist_data[artist2.mbid].custom_name == artist2.sort_name
    assert manager.artist_data[artist1.mbid].custom_original_name == artist1.name
    assert manager.artist_data[artist2.mbid].custom_original_name == artist2.name
    assert manager.artist_data[artist1.mbid].include == artist1.include
    assert manager.artist_data[artist2.mbid].include == artist2.include


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_create_artist_objects_with_db_information(respx_mock):
    # Arrange
    manager = TrackManager()

    artist1 = SimpleArtistDetails(
        name="SimpleArtist1",
        type="Person",
        disambiguation="",
        sort_name="SimpleArtist1",
        id="mock-artist1-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="TestProduct",
        product_id="1",
    )

    artist1_expected = {
        "id": 248,
        "name": "SimpleArtist1",
        "artistId": 41,
        "artist": "CustomSimpleArtist1",
        "franchiseId": 1,
        "franchise": "_",
    }

    artist2 = SimpleArtistDetails(
        name="SimpleArtist2",
        type="Person",
        disambiguation="",
        sort_name="SimpleArtist2",
        id="mock-artist2-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="_",
        product_id="1",
    )

    artist2_expected = {
        "id": 249,
        "name": "SimpleArtist2",
        "artistId": 42,
        "artist": "CustomSimpleArtist2",
        "franchiseId": 1,
        "franchise": "_",
    }

    # Populate artist_data with SimpleArtistDetails
    manager.artist_data[artist1.mbid] = artist1
    manager.artist_data[artist2.mbid] = artist2

    # Mock the DB call to return 200 for the specified artist names with franchiseId

    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/alias",
        params={"name": "SimpleArtist1", "franchiseId": "1"},
    ).mock(return_value=httpx.Response(200, json=[artist1_expected]))

    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/alias",
        params={"name": "SimpleArtist2", "franchiseId": "1"},
    ).mock(return_value=httpx.Response(200, json=[artist2_expected]))

    # Act
    await manager.update_artists_info_from_db()

    # Assert
    assert (
        manager.artist_data[artist1.mbid].custom_name == artist1_expected["artist"]
    ), f"Expected {artist1_expected['artist']}, got {manager.artist_data[artist1.mbid].custom_name}"
    assert (
        manager.artist_data[artist1.mbid].custom_original_name
        == artist1_expected["name"]
    ), f"Expected {artist1_expected['name']}, got {manager.artist_data[artist1.mbid].custom_original_name}"
    assert (
        manager.artist_data[artist1.mbid].id == artist1_expected["artistId"]
    ), f"Expected {artist1_expected['artistId']}, got {manager.artist_data[artist1.mbid].id}"
    assert manager.artist_data[artist1.mbid].include == artist1.include

    assert (
        manager.artist_data[artist2.mbid].custom_name == artist2_expected["artist"]
    ), f"Expected {artist2_expected['artist']}, got {manager.artist_data[artist2.mbid].custom_name}"
    assert (
        manager.artist_data[artist2.mbid].custom_original_name
        == artist2_expected["name"]
    ), f"Expected {artist2_expected['name']}, got {manager.artist_data[artist2.mbid].custom_original_name}"
    assert (
        manager.artist_data[artist2.mbid].id == artist2_expected["artistId"]
    ), f"Expected {artist2_expected['artistId']}, got {manager.artist_data[artist2.mbid].id}"
    assert manager.artist_data[artist2.mbid].include == artist2.include


@pytest.mark.asyncio
async def test_parse_franchise():
    # Arrange
    product_list = [
        {"id": 1, "name": "_"},
        {"id": 2, "name": "Franchise1"},
        {"id": 3, "name": "Franchise2"},
    ]

    # Act & Assert
    result = SimpleArtistDetails.parse_simple_artist_franchise(
        None, product_list[1]["name"], product_list
    )
    assert result == product_list[1]

    result = SimpleArtistDetails.parse_simple_artist_franchise(
        product_list[2]["name"], None, product_list
    )
    assert result == product_list[2]

    result = SimpleArtistDetails.parse_simple_artist_franchise(
        product_list[2]["name"], product_list[1]["name"], product_list
    )
    assert result == product_list[2]

    result = SimpleArtistDetails.parse_simple_artist_franchise(
        None, "NonExistentFranchise", product_list
    )
    assert result == product_list[0]

    result = SimpleArtistDetails.parse_simple_artist_franchise(None, None, product_list)
    assert result == product_list[0]


def test_generate_instance_hash():
    # Arrange
    artist = SimpleArtistDetails(
        name="ArtistName",
        type="Person",
        disambiguation="",
        sort_name="ArtistName",
        id="mock-artist-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="Product",
        product_id="1",
    )
    unique_string = "ArtistName-1"

    # Act
    result = artist.generate_instance_hash(unique_string)

    # Assert
    expected_hash = hashlib.sha256(unique_string.encode()).hexdigest()
    assert result == expected_hash, f"Expected hash {expected_hash}, got {result}"


def test_split_artist():
    # Arrange
    artist_list = [
        "Artist1",
        "Artist2 feat. Artist3 & Artist4",
        "Character1 (CV: Artist5); Character2(CV.Artist6); (Character 3)",
        "Character4(CV.Artist7)",
        "(CV: Artist8)",
        "Character5（CV：Artist9）",
    ]

    expected_result = [
        {"type": "Person", "include": True, "name": "Artist1"},
        {"type": "Person", "include": True, "name": "Artist2"},
        {"type": "Person", "include": True, "name": "Artist3"},
        {"type": "Person", "include": True, "name": "Artist4"},
        {"type": "Person", "include": True, "name": "Artist5"},
        {"type": "Character", "include": False, "name": "Character1"},
        {"type": "Person", "include": True, "name": "Artist6"},
        {"type": "Character", "include": False, "name": "Character2"},
        {"type": "Character", "include": False, "name": "Character 3"},
        {"type": "Person", "include": True, "name": "Artist7"},
        {"type": "Character", "include": False, "name": "Character4"},
        {"type": "Person", "include": True, "name": "Artist8"},
        {"type": "Person", "include": True, "name": "Artist9"},
        {"type": "Character", "include": False, "name": "Character5"},
    ]

    # Act
    result = SimpleArtistDetails.split_artist(artist_list)

    # Assert
    assert len(result) == len(
        expected_result
    ), f"Expected {len(expected_result)} artists, got {len(result)}"
    for i in range(len(result)):
        assert (
            result[i]["name"] == expected_result[i]["name"]
        ), f"Name mismatch at index {i}: expected {expected_result[i]['name']}, got {result[i]['name']}"
        assert (
            result[i]["type"] == expected_result[i]["type"]
        ), f"Type mismatch at index {i} (`{result[i]['name']}`): expected {expected_result[i]['type']}, got {result[i]['type']}"
        assert (
            result[i]["include"] == expected_result[i]["include"]
        ), f"Include mismatch at index {i} (`{result[i]['name']}`): expected {expected_result[i]['include']}, got {result[i]['include']}"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_split_artist_string_into_simple_artist_objects(respx_mock):
    # Arrange
    manager = TrackManager()
    track = TrackDetails("/fake/path/file1.mp3", manager)
    track.album_artist = "Various Artists"
    track.product = None
    track.artist = [
        "Artist1",
        "Artist2 feat. Artist3 & Artist4",
        "Character1 (CV: Artist5); Character2(CV.Artist6); (Character 3)",
        "Character4(CV.Artist7)",
        "(CV: Artist8)",
    ]

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

    expected_simple_artists = [
        {"type": "Person", "name": "Artist1"},
        {"type": "Person", "name": "Artist2"},
        {"type": "Person", "name": "Artist3"},
        {"type": "Person", "name": "Artist4"},
        {"type": "Person", "name": "Artist5"},
        {"type": "Character", "name": "Character1"},
        {"type": "Person", "name": "Artist6"},
        {"type": "Character", "name": "Character2"},
        {"type": "Character", "name": "Character 3"},
        {"type": "Person", "name": "Artist7"},
        {"type": "Character", "name": "Character4"},
        {"type": "Person", "name": "Artist8"},
    ]

    # Act
    await track.create_artist_objects()
    simple_artists = track.artist_details

    # Assert
    assert len(manager.artist_data) == len(
        expected_simple_artists
    ), f"Unexpected number of entries in artist_data"
    assert len(simple_artists) == len(
        expected_simple_artists
    ), f"Expected {len(expected_simple_artists)} simple artists, got {len(simple_artists)}"
    for i, artist in enumerate(simple_artists):
        assert (
            artist.name == expected_simple_artists[i]["name"]
        ), f"Name mismatch at index {i}: expected {expected_simple_artists[i]['name']}, got {artist.name}"
        assert (
            artist.type == expected_simple_artists[i]["type"]
        ), f"Type mismatch at index {i}: expected {expected_simple_artists[i]['type']}, got {artist.type}"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_artist_without_id_not_found_when_saving(respx_mock):
    # Arrange
    manager = TrackManager()
    server_artist_id = 99

    artist = SimpleArtistDetails(
        name="NewSimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="NewSimpleArtist",
        id=None,
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="TestProduct",
        product_id="1",
    )

    artist.custom_name = "NewCustomName"
    manager.artist_data[artist.mbid] = artist

    # Mock the GET requests to simulate that no artist exists
    respx_mock.route(
        method="GET", port=manager.api_port, host=manager.api_host, path="/api/artist"
    ).mock(return_value=httpx.Response(200, text="[]"))

    # Mock the POST requests to create new artist and alias
    respx_mock.route(
        method="POST",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/artist",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": server_artist_id,
                "name": artist.custom_name,
                "aliases": [],
            },
        )
    )

    # Act
    await manager.send_simple_artist_changes_to_db(artist)

    # Assert
    assert respx_mock.calls.call_count == 2
    # verify existing artists
    assert (
        respx_mock.calls[0].request.method == "GET"
    ), "Call to verify artist exist was not of type GET"
    respx_mock.calls[0].request.url.params[
        "name"
    ] == artist.custom_name, "Call to verify artist did not have expected parameters"

    # post new artist
    assert (
        respx_mock.calls[1].request.method == "POST"
    ), "Call to create new artist was not of type POST"
    call_1_content = json.loads(respx_mock.calls[1].request.content.decode())
    assert call_1_content == {
        "Name": artist.custom_name
    }, f"Post body to create new artist did not match expected object"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_artist_without_id_found_by_name_when_saving(respx_mock):
    # Arrange
    manager = TrackManager()
    server_artist_id = 99

    artist = SimpleArtistDetails(
        name="NewSimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="NewSimpleArtist",
        id=-1,
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="TestProduct",
        product_id="1",
    )

    artist.custom_name = "NewCustomName"
    manager.artist_data[artist.mbid] = artist

    # Mock the GET requests to simulate that an artist when searched for name
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/artist",
        params={"name": artist.custom_name},
    ).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": server_artist_id,
                    "name": artist.custom_name,
                    "aliases": [],
                }
            ],
        )
    )

    # Act
    await manager.send_simple_artist_changes_to_db(artist)

    # Assert
    assert respx_mock.calls.call_count == 1
    # verify existing artists
    assert (
        respx_mock.calls[0].request.method == "GET"
    ), "Call to verify artist exist was not of type GET"
    respx_mock.calls[0].request.url.params[
        "name"
    ] == artist.custom_name, "Call to verify artist did not have expected parameters"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_artist_with_id_not_found_when_saving(respx_mock):
    # Arrange
    manager = TrackManager()

    server_artist_name = "ServerCustomName"

    artist = SimpleArtistDetails(
        name="NewSimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="NewSimpleArtist",
        id=35,
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="TestProduct",
        product_id=1,
    )

    artist.custom_name = "NewCustomName"
    manager.artist_data[artist.mbid] = artist

    # Mock first request to not return anything when checking artist by name
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/artist",
        params={"name": artist.custom_name},
    ).mock(return_value=httpx.Response(200, text="[]"))

    # Mock second request to return artist when checking artist by ID
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/artist",
        params={
            "id": artist.id,
        },
    ).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": artist.id,
                    "name": server_artist_name,
                    "aliases": [],
                }
            ],
        )
    )

    # Mock update call to return artist
    respx_mock.route(
        method="PUT",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/artist/id/{artist.id}",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": artist.id,
                "name": artist.custom_name,
                "aliases": [],
            },
        )
    )

    # Act
    await manager.send_simple_artist_changes_to_db(artist)

    # Assert
    assert (
        respx_mock.calls.call_count == 3
    ), "Expected only two calls to check if artist and alias exist."

    # verify if artist exists
    assert (
        respx_mock.calls[0].request.method == "GET"
    ), "Call to verify if an artist exist was not of type GET"
    assert (
        respx_mock.calls[0].request.url.params["name"] == artist.custom_name
    ), "Call to verify if an artist exist used an unexpected parameter"

    assert (
        respx_mock.calls[1].request.method == "GET"
    ), "Call to verify if an artist exist was not of type GET"
    assert respx_mock.calls[1].request.url.params["id"] == str(
        artist.id
    ), "Call to verify if an artist exist used an unexpected parameter"

    # post new artist
    assert (
        respx_mock.calls[2].request.method == "PUT"
    ), "Call to update artist was not of type UPDATE"
    call_2_content = json.loads(respx_mock.calls[2].request.content.decode())
    assert call_2_content == {
        "Name": artist.custom_name
    }, f"Post body to update artist did not match expected object"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_artist_with_id_found_by_id_when_saving(respx_mock):
    # Arrange
    manager = TrackManager()

    artist = SimpleArtistDetails(
        name="NewSimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="NewSimpleArtist",
        id=35,
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="TestProduct",
        product_id=1,
    )

    artist.custom_name = "NewCustomName"
    manager.artist_data[artist.mbid] = artist

    # Mock first request to not return anything when checking artist by name
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/artist",
        params={"name": artist.custom_name},
    ).mock(return_value=httpx.Response(200, text="[]"))

    # Mock second request to return artist when checking artist by ID
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/artist",
        params={
            "id": artist.id,
        },
    ).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": artist.id,
                    "name": artist.custom_name,
                    "aliases": [],
                }
            ],
        )
    )

    # Act
    await manager.send_simple_artist_changes_to_db(artist)

    # Assert
    assert (
        respx_mock.calls.call_count == 2
    ), "Expected only two calls to check if artist and alias exist."

    # verify if artist exists
    assert (
        respx_mock.calls[0].request.method == "GET"
    ), "Call to verify if an artist exist was not of type GET"
    assert (
        respx_mock.calls[0].request.url.params["name"] == artist.custom_name
    ), "Call to verify if an artist exist used an unexpected parameter"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_artist_with_id_found_by_name_when_saving(respx_mock):
    # Arrange
    manager = TrackManager()

    server_artist_id = 99

    artist = SimpleArtistDetails(
        name="NewSimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="NewSimpleArtist",
        id="35",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="TestProduct",
        product_id=1,
    )

    artist.custom_name = "NewCustomName"

    manager.artist_data[artist.mbid] = artist

    # Mock first get request to return artist by name
    respx_mock.route(
        method="GET", port=manager.api_port, host=manager.api_host, path="/api/artist"
    ).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": server_artist_id,
                    "name": artist.custom_name,
                    "aliases": [],
                }
            ],
        )
    )

    # Act
    await manager.send_simple_artist_changes_to_db(artist)

    # Assert
    assert (
        respx_mock.calls.call_count == 1
    ), "Expected only two calls to check if artist and alias exist."

    # verify if artist exists
    assert (
        respx_mock.calls[0].request.method == "GET"
    ), "Call to verify if an artist exist was not of type GET"
    assert (
        respx_mock.calls[0].request.url.params["name"] == artist.custom_name
    ), "Call to verify if an artist exist used an unexpected parameter"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_alias_not_found_when_saving(respx_mock):
    # Arrange
    manager = TrackManager()

    # server_artist_id = 99
    server_artist_name = "Server artist name"

    artist = SimpleArtistDetails(
        name="NewSimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="NewSimpleArtist",
        id=35,
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="_",
        product_id=1,
    )

    manager.artist_data[artist.mbid] = artist

    # Mock request to not return anything when checking alias
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/alias",
        params={"name": artist.name, "franchiseId": artist.product_id},
    ).mock(return_value=httpx.Response(200, text="[]"))

    # Mock the requests create new alias
    respx_mock.route(
        method="POST", port=manager.api_port, host=manager.api_host, path="/api/alias"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 89,
                "name": artist.name,
                "artistId": artist.id,
                "artist": server_artist_name,
                "franchiseId": artist.product_id,
                "franchise": artist.product,
            },
        )
    )

    # Act
    await manager.send_simple_artist_alias_changes_to_db(artist)

    # Assert
    assert respx_mock.calls.call_count == 2

    # verify if artist exists
    assert (
        respx_mock.calls[0].request.method == "GET"
    ), "Call to verify if an artist exist was not of type GET"

    # post new alias
    assert (
        respx_mock.calls[1].request.method == "POST"
    ), "Call to create new alias was not of type POST"
    call_1_content = json.loads(respx_mock.calls[1].request.content.decode())
    assert call_1_content == {
        "Name": artist.name,
        "artistid": artist.id,
        "franchiseid": artist.product_id,
    }, f"Post body to create new alias did not match expected object"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_alias_found_when_saving_points_to_correct_artist(respx_mock):
    # Arrange
    manager = TrackManager()

    # server_artist_id = 99
    server_artist_name = "Server artist name"
    delete_alias_id = 88

    artist = SimpleArtistDetails(
        name="NewSimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="NewSimpleArtist",
        id=35,
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="_",
        product_id=1,
    )

    manager.artist_data[artist.mbid] = artist

    # Mock request to return alias with correct artist id
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/alias",
        params={"name": artist.name, "franchiseId": artist.product_id},
    ).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": delete_alias_id,
                    "name": artist.name,
                    "artistId": artist.id,
                    "artist": server_artist_name,
                    "franchiseId": artist.product_id,
                    "franchise": artist.product,
                }
            ],
        )
    )

    # Act
    await manager.send_simple_artist_alias_changes_to_db(artist)

    # Assert
    assert respx_mock.calls.call_count == 1

    # verify if artist exists
    assert (
        respx_mock.calls[0].request.method == "GET"
    ), "Call to verify if an artist exist was not of type GET"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_alias_found_when_saving_points_to_wrong_artist(respx_mock):
    # Arrange
    manager = TrackManager()

    # server_artist_id = 99
    server_artist_name = "Server artist name"
    delete_alias_id = 88

    artist = SimpleArtistDetails(
        name="NewSimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="NewSimpleArtist",
        id=35,
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="_",
        product_id=1,
    )

    manager.artist_data[artist.mbid] = artist

    # Mock request to return alias with wrong artist id
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/alias",
        params={"name": artist.name, "franchiseId": artist.product_id},
    ).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": delete_alias_id,
                    "name": artist.name,
                    "artistId": 99,
                    "artist": server_artist_name,
                    "franchiseId": artist.product_id,
                    "franchise": artist.product,
                }
            ],
        )
    )

    # Mock the requests to delete and recreate the alias
    respx_mock.route(
        method="DELETE",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/alias/id/{delete_alias_id}",
    ).mock(return_value=httpx.Response(200))

    respx_mock.route(
        method="POST", port=manager.api_port, host=manager.api_host, path="/api/alias"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 89,
                "name": artist.name,
                "artistId": artist.id,
                "artist": server_artist_name,
                "franchiseId": artist.product_id,
                "franchise": artist.product,
            },
        )
    )

    # Act
    await manager.send_simple_artist_alias_changes_to_db(artist)

    # Assert
    assert respx_mock.calls.call_count == 3

    # verify if artist exists
    assert (
        respx_mock.calls[0].request.method == "GET"
    ), "Call to verify if an artist exist was not of type GET"

    # delete old alias
    assert (
        respx_mock.calls[1].request.method == "DELETE"
    ), "Call to delete new alias was not of type DELETE"

    # post new alias
    assert (
        respx_mock.calls[2].request.method == "POST"
    ), "Call to create new alias was not of type POST"
    call_2_content = json.loads(respx_mock.calls[2].request.content.decode())
    assert call_2_content == {
        "Name": artist.name,
        "artistid": artist.id,
        "franchiseid": artist.product_id,
    }, f"Post body to create new alias did not match expected object"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_update_from_simple_artist_dict_sets_has_server_data(respx_mock):
    # Arrange
    manager = TrackManager()

    artist = SimpleArtistDetails(
        name="SimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="SimpleArtist",
        id="mock-artist-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="TestProduct",
        product_id="1",
    )

    manager.artist_data[artist.mbid] = artist

    # Mock the DB call to return artist data
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/alias",
        params={"name": artist.name, "franchiseId": artist.product_id},
    ).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "artistId": 1,
                    "name": "SimpleArtist",
                    "artist": "UpdatedArtist",
                    "franchiseId": 1,
                    "id": 1,
                }
            ],
        )
    )

    # Act
    await manager.update_artists_info_from_db()

    # Assert
    assert artist.has_server_data, "Expected artist.has_server_data to be True"


@pytest.mark.asyncio
async def test_apply_custom_tag_values_handles_semicolon():
    # Arrange
    manager = TrackManager()
    track = TrackDetails("/fake/path/file1.mp3", manager)
    track.title = "test title"
    track.artist = ["test artist1"]

    artist = SimpleArtistDetails(
        name="Artist1",
        type="Person",
        disambiguation="",
        sort_name="Artist1",
        id="mock-artist-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="TestProduct",
        product_id=1,
    )
    artist.custom_name = "CustomArtist1; CustomArtist2"
    track.artist_details.append(artist)

    # Act
    track.apply_custom_tag_values()

    # Assert
    assert track.artist == [
        "CustomArtist1",
        "CustomArtist2",
    ], "The artist names should be split by semicolon"


@pytest.mark.asyncio
async def test_application_handles_file_with_no_tags(respx_mock):
    # Arrange
    manager = TrackManager()
    track = TrackDetails("/fake/path/file_with_no_tags.mp3", manager)
    track.artist = []

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
            ],
        )
    )

    # Act
    await track.create_artist_objects()

    # Assert
    assert track.artist == [], "Expected no artists in track"
    assert track.album_artist is None, "Expected no album artist in track"
    assert track.title is None, "Expected no title in track"
    assert track.album is None, "Expected no album in track"
